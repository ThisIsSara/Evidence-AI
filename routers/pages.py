# routers/pages.py
# All page routes (the HTML pages a user actually sees) live here.
# No AI calls happen in this phase - these routes only render templates
# and load the static demo case file.

import json

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from markupsafe import Markup

from config import TEMPLATES_DIR
from services.investigation_engine import load_demo_case

router = APIRouter()

# Jinja2Templates renders our .html files in the templates/ folder,
# and lets us inject Python data into them (e.g. {{ case.title }}).
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _tojson_filter(value):
    """Safely embed Python data as JSON inside a <script type="application/json"> tag.

    Plain Jinja2 (unlike Flask) has no built-in "tojson" filter, so we add a
    small one here. Escaping "<" prevents the JSON text from accidentally
    closing the surrounding <script> tag.
    """
    return Markup(json.dumps(value).replace("<", "\\u003c"))


templates.env.filters["tojson"] = _tojson_filter


@router.get("/")
def landing_page(request: Request):
    """Render the Evidence AI landing page."""
    return templates.TemplateResponse(request, "index.html")


@router.get("/demo-case")
def demo_case_page(request: Request):
    """Load the fictional demo case from JSON and render the case detail page."""
    case = load_demo_case()
    return templates.TemplateResponse(request, "case_detail.html", {"case": case})


@router.get("/new-investigation")
def new_investigation_page(request: Request):
    """Render the Create New Investigation form.

    The demo case is also loaded here (but not analyzed) so the page's
    "Load Sample Case" button can fill the form with it in JavaScript,
    without duplicating the demo text anywhere.
    """
    demo_case = load_demo_case()
    return templates.TemplateResponse(request, "new_investigation.html", {"demo_case": demo_case})
