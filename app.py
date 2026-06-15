import json
import random
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

with open("data.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

category_meta = {
    "lefty_ocho_xc_hardtail": {
        "name": "Lefty Ocho XC Hardtail",
        "description": "Cross-country hardtail mountain bikes with Lefty Ocho fork",
        "icon": "M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5",
    },
    "lefty_ocho_full_suspension": {
        "name": "Lefty Ocho Full Suspension",
        "description": "Full-suspension cross-country mountain bikes with Lefty Ocho fork",
        "icon": "M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5",
    },
    "lefty_oliver_gravel": {
        "name": "Lefty Oliver Gravel",
        "description": "Gravel and adventure bikes with Lefty Oliver suspension fork",
        "icon": "M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z",
    },
    "lefty_urban_lifestyle": {
        "name": "Lefty Urban Lifestyle",
        "description": "Urban and commuter bikes with rigid Lefty fork",
        "icon": "M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4",
    },
}

models_list = []
for cat_slug, models in raw_data.items():
    for model_name, specs in models.items():
        models_list.append(
            {
                "category_slug": cat_slug,
                "category_name": category_meta.get(cat_slug, {}).get("name", cat_slug),
                "model_name": model_name,
                "specs": specs,
            }
        )


def search_models(query):
    if not query:
        return []
    q = query.lower()
    results = []
    for m in models_list:
        if q in m["model_name"].lower() or q in m["category_name"].lower():
            results.append(m)
            continue
        for key, value in m["specs"].items():
            if isinstance(value, str) and q in value.lower():
                results.append(m)
                break
    return results


@app.route("/")
def home():
    random_models = random.sample(models_list, min(6, len(models_list)))
    return render_template("index.html", models=random_models, categories=category_meta)


@app.route("/catalog")
def catalog():
    return render_template("catalog.html", models=models_list, categories=category_meta)


@app.route("/wiki")
def wiki():
    return render_template("wiki.html", categories=category_meta)


@app.route("/model/<category_slug>/<model_name>")
def model_detail(category_slug, model_name):
    if category_slug not in raw_data or model_name not in raw_data[category_slug]:
        return render_template(
            "error.html",
            code=404,
            title="Model Not Found",
            message=f'No model named "{model_name}" exists in this database.',
        ), 404
    specs = raw_data[category_slug][model_name]
    cat_info = category_meta.get(category_slug, {})
    return render_template(
        "model.html",
        model_name=model_name,
        category_slug=category_slug,
        category_name=cat_info.get("name", category_slug),
        specs=specs,
        categories=category_meta,
    )


@app.route("/search")
def search_page():
    query = request.args.get("q", "")
    results = search_models(query) if query else []
    return render_template(
        "index.html",
        models=results,
        search_query=query,
        is_search=True,
        categories=category_meta,
    )


@app.route("/api/models")
def api_models():
    return jsonify(
        [
            {
                "category": m["category_slug"],
                "category_name": m["category_name"],
                "model": m["model_name"],
                "travel_front_mm": m["specs"].get("travel_front_mm"),
                "travel_rear_mm": m["specs"].get("travel_rear_mm"),
                "frame": m["specs"].get("frame"),
                "fork_model": m["specs"].get("fork_model"),
            }
            for m in models_list
        ]
    )


@app.route("/api/model/<category_slug>/<model_name>")
def api_model_detail(category_slug, model_name):
    if category_slug not in raw_data or model_name not in raw_data[category_slug]:
        return jsonify({"error": "Model not found"}), 404
    return jsonify(
        {
            "category": category_slug,
            "category_name": category_meta.get(category_slug, {}).get(
                "name", category_slug
            ),
            "model": model_name,
            "specs": raw_data[category_slug][model_name],
        }
    )


@app.route("/docs")
def docs():
    return render_template("docs.html", categories=category_meta)


@app.route("/api/search")
def api_search():
    query = request.args.get("q", "")
    results = search_models(query)
    return jsonify(
        [
            {
                "category": m["category_slug"],
                "category_name": m["category_name"],
                "model": m["model_name"],
                "specs": m["specs"],
            }
            for m in results
        ]
    )


@app.errorhandler(400)
def bad_request(e):
    return render_template(
        "error.html",
        code=400,
        title="Bad Request",
        message="The request could not be understood by the server.",
    ), 400


@app.errorhandler(404)
def not_found(e):
    return render_template(
        "error.html",
        code=404,
        title="Page Not Found",
        message="The page you are looking for does not exist or has been moved.",
    ), 404


@app.errorhandler(502)
def bad_gateway(e):
    return render_template(
        "error.html",
        code=502,
        title="Bad Gateway",
        message="The server received an invalid response from an upstream server.",
    ), 502


if __name__ == "__main__":
    app.run(debug=True, port=5000)
