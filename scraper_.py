# scraper.py
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import csv
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import urllib3

from config import SCRAPE_SOURCES, ScrapeSource

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def clean_text(text):
    if not text: 
        return ""
    text = re.sub(r'<[^>]*>', '', text)
    text = re.sub(r'\s+', ' ', text.replace("â€“", "–").replace("\xa0", " ")).strip()
    if len(text) > 400:
        text = text[:397] + "..."
    return text

def fetch_deep_description(session, url, tag, tag_class, headers):
    if not url or "calendar" not in url.lower() and "http" not in url.lower(): 
        return "N/A"
    try:
        res = session.get(url, headers=headers, verify=False, timeout=8)
        if res.status_code == 200:
            sub_soup = BeautifulSoup(res.text, 'html.parser')
            target = sub_soup.find(tag, class_=tag_class) or sub_soup.find(tag)
            if target:
                found_desc = clean_text(target.text)
                if len(found_desc) > 15:
                    return found_desc
    except Exception:
        pass
    return "N/A"

def scrape_source(session, source: ScrapeSource):
    events = []
    print(f"Scraping {source.name} [{source.category}]...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/html, */*',
        'Accept-Language': 'en-US,en;q=0.5'
    }
    
    try:
        res = session.get(source.url, headers=headers, verify=False, timeout=12)
        if res.status_code != 200:
            print(f"  --> Connection failed (Status Code: {res.status_code})")
            return events
            
        # --- Method A: JSON API STREAM EXTRACTION ---
        if source.type == 'json_api':
            data_json = res.json()
            
            # MoMA API Data Blueprint
            if "MoMA" in source.name and "exhibitions" in str(data_json).lower():
                items = data_json.get("exhibitions", data_json.get("items", []))
                for item in items:
                    events.append({
                        "title": clean_text(item.get("title")),
                        "date": clean_text(item.get("date_string", "See Link")),
                        "hours": "Regular Hours",
                        "description": clean_text(item.get("teaser", item.get("description", "N/A"))),
                        "link": urljoin("https://www.moma.org", item.get("url", "")),
                        "category": source.category,
                        "source_site": source.name
                    })
            
            # Art New England WordPress API Blueprint
            elif "New England" in source.name and isinstance(data_json, list):
                for item in data_json:
                    title_dict = item.get("title", {})
                    excerpt_dict = item.get("excerpt", {})
                    events.append({
                        "title": clean_text(title_dict.get("rendered")),
                        "date": "See Link",
                        "hours": "N/A",
                        "description": clean_text(excerpt_dict.get("rendered", "N/A")),
                        "link": item.get("link", source.url),
                        "category": source.category,
                        "source_site": source.name
                    })
                    
            # ICA Boston API Content Blueprint
            elif "ICA" in source.name:
                items = data_json.get("data", data_json if isinstance(data_json, list) else [])
                for item in items:
                    events.append({
                        "title": clean_text(item.get("title", item.get("name"))),
                        "date": clean_text(item.get("date_range", "See Link")),
                        "hours": "Regular Hours",
                        "description": clean_text(item.get("description", item.get("teaser", "N/A"))),
                        "link": urljoin("https://www.icaboston.org", item.get("path", "")),
                        "category": source.category,
                        "source_site": source.name
                    })
        
        # --- Method B: Structured HTML Tags ---
        elif source.type == 'html_tags':
            # FIX: Initialize the soup object for standard web pages right here!
            soup = BeautifulSoup(res.text, 'html.parser')
            
            if source.container_tag and source.container_class:
                items = soup.find_all(source.container_tag, class_=source.container_class)
            else:
                items = soup.find_all(source.title_tag, class_=source.title_class) if source.title_class else soup.find_all(source.title_tag)
            
            for item in items:
                if source.container_tag and source.container_class:
                    title_el = item.find(source.title_tag, class_=source.title_class) or item.find(source.title_tag)
                else:
                    title_el = item
                    
                if not title_el: continue
                title = clean_text(title_el.text)
                
                if not title or len(title) <= 4 or title in ["Menu", "Search", "Contact Us", "In Our Galleries"]: 
                    continue
                
                link_el = item if item.name == 'a' else item.find('a')
                if not link_el and hasattr(title_el, 'find_parent'):
                    link_el = title_el.find_parent('a') or title_el.find('a')
                    
                event_url = urljoin(source.url, link_el['href']) if (link_el and link_el.has_attr('href')) else source.url
                
                date_str = "N/A"
                if source.date_tag and hasattr(item, 'find'):
                    date_el = item.find(source.date_tag, class_=source.date_class) or item.find(source.date_tag)
                    if date_el: date_str = clean_text(date_el.text)
                
                desc_str = "N/A"
                if source.desc_tag and hasattr(item, 'find'):
                    desc_el = item.find(source.desc_tag, class_=source.desc_class) or item.find(source.desc_tag)
                    if desc_el: desc_str = clean_text(desc_el.text)
                
                if (desc_str == "N/A" or len(desc_str) < 15) and source.detail_desc_tag and event_url != source.url:
                    time.sleep(1.5)
                    desc_str = fetch_deep_description(session, event_url, source.detail_desc_tag, source.detail_desc_class, headers)
                
                events.append({
                    "title": title, "date": date_str, "hours": "N/A", "description": desc_str,
                    "link": event_url, "category": source.category, "source_site": source.name
                })
                    
        # --- Method C: Text Block Stream Parsing ---
        elif source.type == 'regex_text':
            soup = BeautifulSoup(res.text, 'html.parser')
            page_text = soup.get_text(" | ", strip=True).replace("â€“", "–").replace("\xa0", " ")
            date_pattern = r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}\s*[–—\-]\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}|Through\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4})"
            tokens = re.split(date_pattern, page_text)
            
            for i in range(1, len(tokens), 2):
                date_str = tokens[i].strip()
                details = tokens[i+1] if (i+1) < len(tokens) else ""
                parts = [p.strip() for p in re.split(r'\s*[\.\|]\s*', details) if p.strip()]
                
                if parts and len(parts[0]) < 100 and "Calendar" not in parts[0]:
                    link_el = soup.find('a', string=lambda s: s and parts[0] in s)
                    event_url = urljoin(source.url, link_el['href']) if link_el else source.url
                    desc_str = " ".join(parts[3:]) if len(parts) > 3 else "N/A"
                    
                    events.append({
                        "title": clean_text(parts[0]), "date": date_str, "hours": "See Link",
                        "description": clean_text(desc_str), "link": event_url, "category": source.category, "source_site": source.name
                    })
                    
    except Exception as e:
        print(f"  --> Error crawling {source.name}: {e}")
        
    print(f"  --> Success: Found {len(events)} events.")
    return events

def run_aggregator():
    session = requests.Session()
    master_raw_list = []
    
    for source in SCRAPE_SOURCES:
        master_raw_list.extend(scrape_source(session, source))
        time.sleep(1.0)
        
    print(f"\nAggregating a total of {len(master_raw_list)} scraped records...")
    
    clustered_data = {}
    for item in master_raw_list:
        norm_key = re.sub(r'[^a-z0-9]', '', item['title'].lower())
        if not norm_key or len(norm_key) < 4: continue
            
        if norm_key not in clustered_data:
            clustered_data[norm_key] = {
                "Title": item['title'], "Category": item['category'], "Dates": item['date'],
                "Hours": item['hours'], "Description": item['description'], "Links": [item['link']],
                "Mentions Count": 1, "Sources": [item['source_site']]
            }
        else:
            if item['source_site'] not in clustered_data[norm_key]["Sources"]:
                clustered_data[norm_key]["Mentions Count"] += 1
                clustered_data[norm_key]["Sources"].append(item['source_site'])
                clustered_data[norm_key]["Links"].append(item['link'])
                
                current_desc = clustered_data[norm_key]["Description"]
                if (current_desc == "N/A" or len(current_desc) < len(item['description'])) and item['description'] != "N/A":
                    clustered_data[norm_key]["Description"] = item['description']
                if clustered_data[norm_key]["Dates"] == "N/A" and item['date'] != "N/A":
                    clustered_data[norm_key]["Dates"] = item['date']

    sorted_events = sorted(clustered_data.values(), key=lambda x: x["Mentions Count"], reverse=True)
    
    csv_filename = "mypath_aggregated_calendar.csv"
    headers = ["Title", "Category", "Dates", "Hours", "Description", "Direct Links", "Internet Mentions Count", "Sources Tracking"]
    
    with open(csv_filename, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        for ev in sorted_events:
            writer.writerow([ev["Title"], ev["Category"], ev["Dates"], ev["Hours"], ev["Description"], " | ".join(ev["Links"]), ev["Mentions Count"], ", ".join(ev["Sources"])])
            
    print(f"🎉 Complete! Saved to '{csv_filename}'.")

if __name__ == "__main__":
    run_aggregator()