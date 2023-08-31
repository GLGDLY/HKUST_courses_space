import os
from json import dumps, loads
from re import compile as re_compile

from github import Github

from md_parser import CourseReadmeIO, ReadmeIO, ReviewParser
from fetch import fetch_course_intro

title_regex = re_compile(r"\[Review]: *(\s\S*)")
with open("courses.json", "r") as cf:
    all_courses = loads(cf.read())


def main():
    # fetch issue data
    repo = Github(os.environ["GITHUB_TOKEN"]).get_repo(os.environ["GITHUB_REPOSITORY"])
    issue_id = int(os.environ["ISSUE_NUMBER"])
    issue = repo.get_issue(number=issue_id)
    issue_author = "@" + issue.user.login

    try:
        # get title
        matching = title_regex.match(issue.title)
        if not matching:
            issue.edit(state="closed", labels=["Invalid"])
            issue.create_comment(
                "ERROR: Title is invalid! Please use the format: `[Review]: <review title>`"
            )
            return False, "ERROR: Title is invalid!"
        title = matching.group(1)

        # get body
        body = issue.body
        body = ReviewParser(body)

        # render template
        rendered = body.render(title, issue_author)

        # check if course exists in previous records
        if body.course_code not in all_courses:
            # update review data to courses.json
            all_courses[body.course_code] = {
                "intro": fetch_course_intro(body.course_code),
                "rating_number": 1,
                "content_rating_sum": body.rating_content,
                "teaching_rating_sum": body.rating_teaching,
                "grade_rating_sum": body.rating_grade,
                "workload_rating_sum": body.rating_workload,
                "overall_rating_sum": body.rating_overall,
                "reviews": {issue_id: title},
            }
            with open("courses.json", "w") as f:
                f.write(dumps(all_courses))

            # add course to README.md
            readme = ReadmeIO()
            readme.write(all_courses)

            # create course folder
            os.makedirs("./reviews/" + body.course_code)
        else:
            all_courses[body.course_code]["rating_number"] += 1
            all_courses[body.course_code]["content_rating_sum"] += body.rating_content
            all_courses[body.course_code]["teaching_rating_sum"] += body.rating_teaching
            all_courses[body.course_code]["grade_rating_sum"] += body.rating_grade
            all_courses[body.course_code]["workload_rating_sum"] += body.rating_workload
            all_courses[body.course_code]["overall_rating_sum"] += body.rating_overall
            all_courses[body.course_code]["reviews"][issue_id] = title
            with open("courses.json", "w") as f:
                f.write(dumps(all_courses))

        # save rendered review to ./reviews/<course_code>/<id>.md
        with open(
            "./reviews/" + body.course_code + "/" + str(issue_id) + ".md", "w"
        ) as f:
            f.write(rendered)

        # create or update course->README.md
        course_readme = CourseReadmeIO(body.course_code, all_courses[body.course_code]["intro"])
        course_readme.write(all_courses[body.course_code], body.course_code)

        # add labels and close issue
        issue.create_comment("review has been rendered successfully.")
        issue.edit(state="closed", labels=[body.course_code])

    except Exception as e:
        issue.edit(state="closed", labels=["Invalid"])
        issue.create_comment("render review error: " + str(e))
        return False, "ERROR: " + str(e)

    return True, ""


if __name__ == "__main__":
    ret, reason = main()

    if not ret:
        exit(reason)
