import xlsxwriter
from github import Auth, Github
from xlsxwriter import workbook

if __name__ == '__main__':
    prs = [
    "https://github.com/oracle/graal/pull/8836",
    ]
    auth = Auth.Token("")
    g = Github(auth=auth)
    workbook = xlsxwriter.Workbook("comments-leftover.xlsx")
    worksheet = workbook.add_worksheet("comments")
    index = 1
    for pr in prs:
        comments = set()
        worksheet.write("A" + str(index), pr)
        info = pr.replace("https://", "").split("/")
        repo_name = info[1] + "/" + info[2]
        id = info[4]
        repo = g.get_repo(repo_name)
        pr_obj = repo.get_pull(int(id))
        for comment in pr_obj.get_issue_comments():
            if comment.user.login == "<<double blind>>":
                continue
            url = comment.url
            text = comment.body
            comments.add((url, text))
            # # print(comment.body)
            # worksheet.write("B" + str(index), url)
            # worksheet.write("C" + str(index), text)
            # index = index + 1
        for comment in pr_obj.get_review_comments():
            print(comment.user)
            if comment.user.login == "<<double blind>>":
                continue
            url = comment.url
            text = comment.body
            comments.add((url, text))
            # print(comment.body)
            # worksheet.write("B" + str(index), url)
            # worksheet.write("C" + str(index), text)
            # index = index + 1
        for review in pr_obj.get_reviews():

            url = review.html_url
            text = review.body
            if text:
                comments.add((url, text))
            # worksheet.write("C" + str(index), body)
            # index = index + 1
            for comment in pr_obj.get_single_review_comments(review.id):
                print(comment.user)
                if comment.user.login == "<<double blind>>":
                    continue
                url = comment.url
                text = comment.body
                comments.add((url, text))
                # print(comment.body)
                # worksheet.write("B" + str(index), url)
                # worksheet.write("C" + str(index), text)
                # index = index + 1
        for comment in pr_obj.get_comments():
            print(comment.user)
            if comment.user.login == "<<double blind>>":
                continue
            url = comment.url
            text = comment.body
            comments.add((url, text))
            # print(comment.body)
            # worksheet.write("B" + str(index), url)
            # worksheet.write("C" + str(index), text)
            # index = index + 1
        for comment in comments:
            worksheet.write("B" + str(index), comment[0])
            worksheet.write("C" + str(index), comment[1])
            index = index + 1
    worksheet.autofit()
    workbook.close()
