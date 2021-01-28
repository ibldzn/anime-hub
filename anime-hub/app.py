import httpx
import asyncio
import html.parser
import werkzeug.exceptions
from collections import defaultdict
from flask import Flask, render_template, request


loop = asyncio.get_event_loop()
app = Flask(__name__)

sites = [
    "samehadaku.vip",
    "meownime.moe",
    # "oploverz.in";does not work if request was made outside of Indonesia (probably Asia, I haven't really tested it)
    "drivenime.com",
    # "awsubs.co", ; dead.
    "animeindo.video",
    "nekonime.video",
    "nimegami.com",
]


@app.errorhandler(werkzeug.exceptions.HTTPException)
def on_error(exception: werkzeug.exceptions.HTTPException):
    return render_template("error.html", error_msg=f"Status code {exception.code}: {exception.description}"), exception.code


async def download_results(site: str, params: dict):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0"}
    async with httpx.AsyncClient(headers=headers) as client:
        response = await client.get(f"https://{site}/wp-json/wp/v2/search", params=params)
        return {site: response.json()} if not response.is_error else None

        """
        # this is better if request was sent from the client.
        ret = list()
        cnt = 0  # request counter

        while True:
            if (cnt + 1) % 2 == 0:
                await asyncio.sleep(2)  # prevent flooding the server to avoid IP Ban
            
            response = await client.get(f"https://{site}/wp-json/wp/v2/search", params=params)
            cnt += 1
            data = response.json()

            if response.is_error or not data:
                break

            ret.extend(data)
            params["page"] += 1
        
        return {site: ret}
        """


async def get_search_results(sources: list, params: dict):
    return await asyncio.gather(*[download_results(source, params) for source in sources])


@app.route("/search")
def search():
    anime = request.args["anime"]
    if not anime:
        return render_template("error.html", error_msg="Status code 400: `anime` parameter cannot be empty!"), 400

    sources = request.args.getlist("sources")
    if not sources:
        sources = sites

    data = defaultdict(list)

    params = {
            "search": anime,
            "per_page": 100,
            "page": 1
        }
    search_results = loop.run_until_complete(get_search_results(sources, params))

    for search_result in search_results:
        for site, results in search_result.items():
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
