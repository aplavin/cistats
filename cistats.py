from flask import Flask, render_template
import hglib
from datetime import datetime

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


def remove_repeated(cs1, cs2):
    cs1_old = cs1
    cs1 = []
    for c1 in cs1_old:
        if not any(c1['desc'] == c2['desc'] for c2 in cs2):
            cs1.append(c1)
    return cs1


@app.route('/')
def index():
    user = 'me@aplavin.ru'

    commits = {rid: get_commits(repos[rid], user) for rid in repos}
    for i, rid in list(enumerate(repos_order))[:0:-1]:
        commits[rid] = remove_repeated(commits[rid], commits[repos_order[i - 1]])

    return render_template('index.html', commits=commits, repos=repos)


repos = {
    'main': Repo('/home/alexander/hg_related/hg', 'http://selenic.com/hg'),
    'crew': Repo('/home/alexander/hg_related/hg-crew', 'http://hg.intevation.org/mercurial/crew'),
    'mine': Repo('/home/alexander/hg_related/hg_fork', 'http://hg.aplavin.ru/hg_fork'),
}
repos_order = ['main', 'crew', 'mine']

app.jinja_env.filters['timedelta'] = timesince
if __name__ == '__main__':
    app.run(debug=True)
