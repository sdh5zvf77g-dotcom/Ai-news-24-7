import json, re, html, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

FEEDS = [
 ("OpenAI","https://openai.com/news/rss.xml"),
 ("Google AI","https://blog.google/technology/ai/rss/"),
 ("Hugging Face","https://huggingface.co/blog/feed.xml"),
 ("TechCrunch","https://techcrunch.com/category/artificial-intelligence/feed/"),
 ("The Verge","https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
 ("VentureBeat","https://venturebeat.com/category/ai/feed/"),
 ("Hacker News","https://hnrss.org/newest?q=Claude+OR+GPT+OR+Gemini+OR+Llama+OR+Qwen+OR+DeepSeek+OR+Mistral+OR+Grok&points=80"),
]
COMPANIES = {
 "Anthropic":["anthropic","claude","fable","mythos"],
 "OpenAI":["openai","gpt","chatgpt","sora","codex"],
 "Google":["google","gemini","deepmind","gemma"],
 "Meta":["meta ai","llama","muse"],
 "xAI":["xai","grok"],
 "Mistral":["mistral"],
 "DeepSeek":["deepseek"],
 "Qwen":["qwen","alibaba"],
 "Moonshot":["kimi","moonshot"],
 "Nvidia":["nvidia","nemotron"],
 "Microsoft":["microsoft","copilot","phi-"],
}
MODEL_WORDS = ["model","gpt","claude","gemini","llama","qwen","deepseek","mistral","grok","kimi","llm","release","launch","benchmark","open-source","open weights"]

def tag(text):
    t = text.lower()
    for c, ks in COMPANIES.items():
        if any(k in t for k in ks): return c
    return "Other"

def clean(s):
    s = re.sub(r"<[^>]+>", " ", html.unescape(s or ""))
    return re.sub(r"\s+", " ", s).strip()[:220]

def when(s):
    try: d = parsedate_to_datetime(s)
    except Exception:
        try: d = datetime.fromisoformat(s.replace("Z","+00:00"))
        except Exception: return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)

def fetch(name, url):
    req = urllib.request.Request(url, headers={"User-Agent":"ai-news-app/1.0"})
    root = ET.fromstring(urllib.request.urlopen(req, timeout=20).read())
    out = []
    for it in root.iter():
        tg = it.tag.split("}")[-1]
        if tg not in ("item","entry"): continue
        g = lambda n: next((c for c in it if c.tag.split("}")[-1]==n), None)
        title = clean(g("title").text if g("title") is not None else "")
        l = g("link"); link = (l.get("href") or l.text or "").strip() if l is not None else ""
        sm = g("description") or g("summary") or g("content")
        summ = clean(sm.text if sm is not None else "")
        dt = g("pubDate") or g("published") or g("updated")
        d = when(dt.text) if dt is not None else None
        if not (title and link and d): continue
        blob = title + " " + summ
        if not any(w in blob.lower() for w in MODEL_WORDS): continue
        out.append({"title":title,"link":link,"source":name,"summary":summ,
                    "company":tag(blob),"date":d.astimezone(timezone.utc).isoformat()})
    return out

items = []
for name, url in FEEDS:
    try: items += fetch(name, url)
    except Exception as e: print("skip", name, e)

try: old = json.load(open("news.json")).get("items", [])
except Exception: old = []
seen = {i["link"] for i in items}
items += [o for o in old if o["link"] not in seen]
items.sort(key=lambda i: i["date"], reverse=True)
json.dump({"updated":datetime.now(timezone.utc).isoformat(),"items":items[:80]}, open("news.json","w"), indent=1)
print(len(items[:80]), "items")
