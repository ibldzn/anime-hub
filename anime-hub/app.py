import requests
import html.parser
import werkzeug.exceptions
from collections import defaultdict
from flask import Flask, render_template, request


app = Flask(__name__)

sites = [
    "samehadaku.vip",
    "meownime.moe",
    # "oploverz.in";does not work if request was made outside of Indonesia (probably Asia, I haven't really tested it)
    "drivenime.com",
    "awsubs.co",
    "animeindo.video",
    "nekonime.video",
    "nimegami.com",
]


@app.errorhandler(werkzeug.exceptions.HTTPException)
def on_error(exception: werkzeug.exceptions.HTTPException):
    return render_template("error.html", error_msg=f"Status code {exception.code}: {exception.description}"), exception.code


@app.route("/search")
def search():
    anime = request.args["anime"]
    if not anime:
        return render_template("error.html", error_msg="Status code 400: `anime` parameter cannot be empty!"), 400

    sources = request.args.getlist("sources")
    if not sources:
        sources = sites

    data = defaultdict(list)
    with requests.Session() as session:
        session.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0"
        params = {
            "search": anime,
            "per_page": 100
        }

        for site in sources:
            r = session.get(f"https://{site}/wp-json/wp/v2/search", params=params)
            if not r.ok:
                continue

            results = r.json()

            for result in results:
                data[site].append({
                    "title": html.parser.unescape(result["title"]),
                    "url": result["url"]
                })

    return render_template("results.html",
                           data=dict(
                                sorted(
                                    data.items(),
                                    key=lambda x: (x[1][0]["title"], len(x[1][0]["title"]))
                                )
                           ),
                           anime=anime)


@app.route('/')
def index():
    return render_template("index.html", sites=sites)


if __name__ == "__main__":
    app.run()
