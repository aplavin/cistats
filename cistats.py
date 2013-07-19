from flask import Flask, render_template, request
import hglib
from datetime import datetime
import xmlrpclib
import re

app = Flask(__name__)
hglib.HGPATH = '/usr/local/bin/hg'


def timesince(value, default="just now"):
    now = datetime.now()
    diff = now - value
    periods = (
        (diff.days / 365, "year", "years"),
        (diff.days / 30, "month", "months"),
        (diff.days / 7, "week", "weeks"),
        (diff.days, "day", "days"),
        (diff.seconds / 3600, "hour", "hours"),
        (diff.seconds / 60, "minute", "minutes"),
        (diff.seconds, "second", "seconds"),
    )
    for period, singular, plural in periods:
        if period:
            return "%d %s ago" % (period, singular if period == 1 else plural)
    return default


class Repo(object):
    def __init__(self, path, url):
        self.path = path
        self.url = url


def get_commits(repo, user):
    with hglib.open(repo.path) as client:
        revs = client.log(user=user)
    return [{'desc': r[5], 'dt': r[6], 'hash': r[1]} for r in revs]


def get_patchbombed(user):
    rpc = xmlrpclib.Server('http://patchwork.serpentine.com/xmlrpc/')
    person_id = rpc.person_list(user, 0)[0]['id']
    state_id = rpc.state_list('New', 0)[0]['id']
    patches = rpc.patch_list({'submitter_id': person_id, 'state_id': state_id})
    return [{'desc': re.sub(r'^\[.*?\]\s*', '', p['name'])} for p in patches]


def commit_in(ci, cis):
    lst = [c for c in cis if c['desc'].splitlines()[0] == ci['desc'].splitlines()[0]]
    if lst:
        if 'hash' in lst[0]:
            return lst[0]['hash']
        else:
            return True
    else:
        return False


@app.route('/')
def index():
    user = 'me@aplavin.ru'

    commits = {rid: get_commits(repos[rid], user) for rid in repos}
    commits['pbomb'] = [ci for ci in get_patchbombed(user) if commit_in(ci, commits['mine'])]

    my_commits = [
        (
            ci,
            [
                rid
                for rid in commits
                if commit_in(ci, commits[rid])
            ]
        )
        for ci in commits['mine']
    ]

    commit_cnts = {rid: len(commits[rid]) for rid in commits}
    commit_cnts['not_accepted'] = len([c for c, crepos in my_commits if len(crepos) == 1])

    return render_template(
        'index.html',
        all_commits=commits,
        commits=my_commits,
        commit_cnts=commit_cnts,
        repos=repos,
        debug='debug' in request.args
    )


repos = {
    'main': Repo('/home/alexander/hg_related/hg', 'http://selenic.com/hg'),
    'crew': Repo('/home/alexander/hg_related/hg-crew', 'http://hg.intevation.org/mercurial/crew'),
    'mine': Repo('/home/alexander/hg_related/hg_fork', 'http://hg.aplavin.ru/hg_fork'),
}

app.jinja_env.filters['timedelta'] = timesince
app.jinja_env.filters['firstline'] = lambda s: (s.splitlines() + ['(none)'])[0]

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
