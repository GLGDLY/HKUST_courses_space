import requests
import re

course_title_regex = re.compile(r"<h2>(\S+) (\S+) - (.+) \(.+\)</h2>")


def fetch_course_intro(course_code: str) -> str:
    course_prefix = re.match("[A-Z]+", course_code)
    if not course_prefix:
        raise ValueError("Invalid course code")
    course_prefix = course_prefix.group(0)
    if len(course_prefix) != 4:
        raise ValueError("Invalid course code")
    course_url = f"https://w5.ab.ust.hk/wcq/cgi-bin/2310/subject//{course_prefix}"
    course_page = requests.get(course_url)
    all_course_intros = course_title_regex.findall(course_page.text)
    for course_intro in all_course_intros:
        if course_intro[0] + course_intro[1] == course_code:
            return course_intro[2]
    return ""
