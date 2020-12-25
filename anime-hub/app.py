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


@app.errorhandler(Exception)
def on_error(exception):
    if exception is werkzeug.exceptions.BadRequestKeyError:
        error_msg = "400 Bad Request: The server did not understand the request."
        status_code = 400
    elif exception is werkzeug.exceptions.NotFound:
        error_msg = "404 Not Found: The requested URL was not found on the server."
        status_code = 404
    else:
        error_msg = "500 Internal Server Error: The request was not completed. Please try again."
        status_code = 500

    return render_template("error.html", error_msg=error_msg, status_code=status_code)


@app.route("/search")
def search():
    anime = request.args["anime"]
    sources = request.args.getlist("sources")
    if len(sources) == 0:
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

    return render_template("results.html", data=dict(
                                                    sorted(
                                                        data.items(),
                                                        key=lambda x: (x[1][0]["title"], len(x[1][0]["title"]))
                                                    )
                                                ), anime=anime)


@app.route('/')
def index():
    return render_template("index.html", sites=sites)


if __name__ == "__main__":
    app.run()
