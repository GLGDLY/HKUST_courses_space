import asyncio
import re
from ssl import create_default_context

from aiohttp import ClientSession, TCPConnector

course_title_regex = re.compile(r"<h2>(\S+) (\S+) - (.+) \(.+\)</h2>")

sslcontext = create_default_context()
sslcontext.set_ciphers("AES256-GCM-SHA384")


async def __fetch_course_intro(course_url: str) -> str:
    async def new_connector(*args, **kwargs):
        return TCPConnector(*args, **kwargs)

    connector = await new_connector()
    async with ClientSession(connector=connector) as session:
        async with session.get(
            course_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/116.0.0.0 Safari/537.36"
            },
            ssl=sslcontext,
        ) as resp:
            return await resp.text()


def fetch_course_intro(course_code: str) -> str:
    course_prefix = re.match("[A-Z]+", course_code)
    if not course_prefix:
        raise ValueError("Invalid course code")
    course_prefix = course_prefix.group(0)
    if len(course_prefix) != 4:
        raise ValueError("Invalid course code")
    course_url = f"https://w5.ab.ust.hk/wcq/cgi-bin/2310/subject/{course_prefix}"
    try:
        course_page = asyncio.run(__fetch_course_intro(course_url))
        all_course_intros = course_title_regex.findall(course_page)
        for course_intro in all_course_intros:
            if course_intro[0] + course_intro[1] == course_code:
                return course_intro[2]
    except Exception as e:
        print("Error fetching course intro: " + str(e))
    return ""


print(fetch_course_intro("COMP1021"))
