# config.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class ScrapeSource:
    name: str
    url: str
    type: str = "html_tags"
    
    title_tag: Optional[str] = None
    title_class: Optional[str] = None
    
    date_tag: Optional[str] = None
    date_class: Optional[str] = None
    
    hours_tag: Optional[str] = None
    hours_class: Optional[str] = None
    
    desc_tag: Optional[str] = None
    desc_class: Optional[str] = None
    
    detail_desc_tag: Optional[str] = None
    detail_desc_class: Optional[str] = None
    
    container_tag: Optional[str] = None
    container_class: Optional[str] = None
    
    category: str = "FineArt"

# =====================================================================
# THE MASTER SOURCE REGISTRY
# =====================================================================
SCRAPE_SOURCES = [
    ScrapeSource(
        name="Art Radar",
        url="https://artradar.org/calendar",
        type="regex_text",
        category="FineArt"
    ),
    ScrapeSource(
        name="Art New England",
        url="https://artnewengland.com/exhibitions/",
        title_tag="h2",
        category="FineArt"
    ),
    ScrapeSource(
        name="The Umbrella Arts - Exhibitions",
        url="https://theumbrellaarts.org/current-exhibition",
        title_tag="h1",
        category="FineArt"
    ),
    ScrapeSource(
        name="MoMA - Calendar",
        url="https://www.moma.org/calendar/",
        title_tag="h3",
        category="FineArt"
    ),
    # ScrapeSource(
    #     name="Harvard Art Museums",
    #     url="https://calendar.college.harvard.edu/group/harvard_art_museums",
    #     title_tag="h3",
    #     detail_desc_tag="div", detail_desc_class="em-description",
    #     category="FineArt"
    # ),
    
    # --- ICA Boston Section ---
    ScrapeSource(
        name="ICA Boston - Main Exhibitions",
        url="https://www.icaboston.org/exhibitions/",
        title_tag="a", # Target the clickable title container directly
        container_tag="div", container_class="promo__content",
        category="FineArt"
    ),
    ScrapeSource(
        name="ICA Boston - Current Shows Block",
        url="https://www.icaboston.org/exhibitions/#block-views-exhibitions-block-1",
        title_tag="a",
        container_tag="div", container_class="promo__content",
        category="FineArt"
    ),
    ScrapeSource(
        name="ICA Boston - Upcoming Shows Block",
        url="https://www.icaboston.org/exhibitions/#block-views-exhibitions-block-2",
        title_tag="a",
        container_tag="div", container_class="promo__content",
        category="FineArt"
    ),
    ScrapeSource(
        name="ICA Boston - Talks & Courses",
        url="https://www.icaboston.org/calendar/talkscourses/",
        title_tag="a",
        container_tag="div", container_class="promo__content",
        category="FineArt"
    )
]