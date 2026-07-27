"""
Render.com Scraper - Chạy như web service
Expose API endpoint để lấy data
"""

from flask import Flask, jsonify
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
import re
import os
from datetime import datetime

app = Flask(__name__)

# Cache data
CACHE = {
    "offers": [],
    "last_update": None,
    "status": "idle"
}


def parse_offers(html):
    """Parse offers từ HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    rows = soup.find_all('tr', {'class': 'ant-table-row'})
    
    offers = []
    for row in rows:
        try:
            cells = row.find_all('td')
            if len(cells) < 6:
                continue
            
            name_cell = cells[1]
            time_cell = cells[2]
            type_cell = cells[3]
            commission_cell = cells[4]
            action_cell = cells[5]
            
            name_link = name_cell.find('a')
            name = name_link.text.strip() if name_link else ""
            
            img = name_cell.find('img')
            image_url = img['src'] if img else ""
            
            time_text = time_cell.get_text(strip=True)
            matches = re.findall(r'(\d{2}-\d{2}-\d{4})', time_text)
            start_date = matches[0] if len(matches) >= 1 else ""
            end_date = matches[1] if len(matches) >= 2 else ""
            
            offer_type = type_cell.text.strip()
            commission = commission_cell.text.strip()
            
            detail_link = action_cell.find('a', href=True)
            detail_url = detail_link['href'] if detail_link else ""
            offer_id = re.search(r'/(\d+)\?', detail_url).group(1) if detail_url and re.search(r'/(\d+)\?', detail_url) else ""
            
            offers.append({
                "id": offer_id,
                "name": name,
                "image_url": image_url,
                "start_date": start_date,
                "end_date": end_date,
                "type": offer_type,
                "commission": commission,
                "detail_url": f"https://affiliate.shopee.vn{detail_url}" if detail_url.startswith('/') else detail_url
            })
        except:
            continue
    
    return offers


async def scrape_offers():
    """Scrape offers với Playwright"""
    try:
        async with async_playwright() as p:
            print("Launching browser...")
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            # Load cookies từ environment
            cookies_str = os.getenv('SHOPEE_COOKIES')
            if cookies_str:
                cookies = json.loads(cookies_str)
                await context.add_cookies(cookies)
            
            page = await context.new_page()
            
            print("Navigating to Shopee...")
            await page.goto('https://affiliate.shopee.vn/offer/shopee_offer', 
                          wait_until='domcontentloaded', timeout=30000)
            
            # Check redirect
            url = page.url
            if 'verify' in url or 'captcha' in url:
                await browser.close()
                return {
                    "success": False,
                    "error": "Blocked by anti-bot (CAPTCHA)",
                    "message": "Cookies expired or invalid"
                }
            
            # Đợi table
            await asyncio.sleep(3)
            try:
                await page.wait_for_selector('.ant-table-tbody', timeout=10000)
            except:
                pass
            
            # Scroll
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(1)
            
            # Lấy HTML
            html = await page.content()
            await browser.close()
            
            # Parse
            offers = parse_offers(html)
            
            return {
                "success": True,
                "offers": offers,
                "count": len(offers),
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.route('/')
def index():
    """API info"""
    return jsonify({
        "name": "Shopee Affiliate Scraper API",
        "version": "1.0",
        "endpoints": {
            "/api/scrape": "Scrape offers (fresh)",
            "/api/offers": "Get cached offers",
            "/api/health": "Health check"
        }
    })


@app.route('/api/health')
def health():
    """Health check"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "cache_status": CACHE["status"],
        "last_update": CACHE["last_update"]
    })


@app.route('/api/offers')
def get_offers():
    """Lấy offers từ cache"""
    return jsonify({
        "success": True,
        "offers": CACHE["offers"],
        "count": len(CACHE["offers"]),
        "last_update": CACHE["last_update"],
        "cached": True
    })


@app.route('/api/scrape')
def scrape():
    """Scrape fresh data"""
    global CACHE
    
    print("Starting scrape...")
    CACHE["status"] = "scraping"
    
    result = asyncio.run(scrape_offers())
    
    if result.get("success"):
        CACHE["offers"] = result["offers"]
        CACHE["last_update"] = result["timestamp"]
        CACHE["status"] = "success"
        print(f"Scraped {len(result['offers'])} offers")
    else:
        CACHE["status"] = "error"
        print(f"Error: {result.get('error')}")
    
    return jsonify(result)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    
    print("=" * 60)
    print("SHOPEE SCRAPER API - Render.com")
    print("=" * 60)
    print(f"Starting on port {port}...")
    print()
    
    app.run(host='0.0.0.0', port=port)
