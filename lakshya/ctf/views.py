from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import datetime
import time
from .models import UserProfile, Questions, Submission
from django.contrib.auth.models import User, auth

endtime = 0
duration = 2700

ques = 4


def index(request):
    return render(request, 'ctf/index.html')


def error(request):
    return render(request, 'ctf/404.html')


def about(request):
    try:
        user = User.objects.get(username=request.user.username)
    except User.DoesNotExist:
        user = None
    return render(request, 'ctf/about.html', context={'curr_user': user})


def inst(request):
    return render(request, 'ctf/instructions.html')


def hint(request):
    if request.method == 'POST':
        question = Questions.objects.get(Qid=request.POST.get('id'))
        print("hint of" + question.Qtitle)
        hint1 = question.Hint
        print(hint1)
        questionPoints = question.points
        user = User.objects.get(username=request.user.username)
        userprofile = UserProfile.objects.get(user=user)
        try:
            solved = Submission.objects.get(question=question, user=userprofile)
            print(solved)
            return HttpResponse(hint1)
        except Submission.DoesNotExist:
            solved = Submission()
            print("--marks")
            userprofile.score -= questionPoints * 0.1
            print(userprofile.score)
            solved.question = question
            solved.user = userprofile
            solved.curr_score = userprofile.score
            solved.save()
            userprofile.save()
            return HttpResponse(hint1)
    return render(request, 'ctf/404.html')


def check(request):
    user = User.objects.get(username=request.user.username)
    userprofile = UserProfile.objects.get(user=user)
    questions = Questions.objects.all().order_by('Qid')
    if request.method == 'POST':
        req = request.POST
        Qid = req.get('Qid')
        flag = req.get('flag')
        level = req.get('customRadio')
        quest = Questions.objects.get(Qid=int(Qid))
        quest.Qid = Qid
        if level == None:
            return HttpResponse("-1")
        else:
            quest.level = level
            if level == 'E':
                quest.Easy += 1
            elif level == 'M':
                quest.Med += 1
            else:
                quest.Hard += 1
            print(quest.Easy, quest.Med, quest.Hard)
            quest.save()

            solved = Submission.objects.filter(question=quest, user=userprofile, solved=1)

            if flag == quest.flag:
                if not solved:
                    solved = Submission()
                    userprofile.score += quest.points
                    solved.question = quest
                    solved.user = userprofile
                    solved.curr_score = userprofile.score
                    #global solvedque
                    #solvedque[quest.Qid] = 'solved'
                    print(Qid)
                    sec = calc()
                    sec = duration - sec
                    solved.sub_time = time.strftime("%H:%M:%S", time.gmtime(sec))
                    userprofile.latest_sub_time = solved.sub_time
                    # solved.sub_time = '{}:{}:{}'.format(hour, min, sec)
                    print(solved.sub_time)
                    quest.solved_by += 1
                    solved.solved = 1
                    userprofile.totlesub += 1

                    request.session["solved"][int(Qid) - 1] = 'solved'
                    userprofile.save()
                    solved.save()
                    quest.save()
                    request.session.save()

                    print("FLAG IS CORRECT!")
                    return HttpResponse('1')

                else:
                    return HttpResponse('2')
            else:
                print("INCORRECT")
                return HttpResponse('0')
    return HttpResponse("")


def timer():
    start = datetime.datetime.now()
    starttime = start.hour * 60 * 60 + start.minute * 60 + start.second
    global duration
    global endtime
    endtime = starttime + int(duration)
    print(starttime)
    return start


def calc():
    global endtime
    now = datetime.datetime.now()
    nowsec = now.hour * 60 * 60 + now.minute * 60 + now.second
    diff = endtime - nowsec
    print(diff)
    if nowsec <= endtime:
        return diff
    else:
        return 0


def register(request):
    if request.method == 'POST':
        recid = request.POST.get('reciept_id')
        username = request.POST.get('username')
        password = request.POST.get('password')
        score = 0

        try:
            user = User.objects.get(username=username)
            return render(request, 'ctf/register.html', {'error': "Username Has Already Been Taken"})
        except User.DoesNotExist:
            user = User.objects.create_user(username=username, password=password)
            # time = timer()
            userprofile = UserProfile(user=user, Rid=recid, score=score)
            userprofile.save()
            timer()
            login(request, user)

            return redirect("inst")

    elif request.method == 'GET':
        return render(request, 'ctf/register.html')


def login1(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            userprofile = UserProfile.objects.get(user=user)
            userprofile.time = timer()
            userprofile.save()
            return redirect("inst")
        else:
            messages.error(request, 'Invalid credentials!')

    return render(request, 'ctf/login.html')


@login_required(login_url="/login")
def Quest(request):
    var = calc()
    if var != 0:
        request.session["solved"] = ['' for i in range(ques)]
        user = User.objects.get(username=request.user.username)
        userprofile = UserProfile.objects.get(user=user)
        questions = Questions.objects.all().order_by('Qid')
        submission = Submission.objects.values().filter(user=userprofile).order_by('question_id')

        # solvedque = []
        #
        # for que in questions:
        #     solvedque.append('')

        for sub in submission:
            if sub['solved'] == 1:
                request.session["solved"][sub['question_id']-1] = 'solved'
                # solvedque[sub['question_id'] - 1] = 'solved'
        request.session.save()
        zipped = zip(questions, request.session["solved"])
        print(zipped)
        return render(request, 'ctf/quests.html',
                      {'questions': questions,'zipped': zipped, 'user': userprofile, 'time': var, 'submission': submission})
    else:
        return render(request, 'ctf/404.html')


def logout(request):
    auth.logout(request)
    return redirect('/leaderboard')


def leaderboard(request):
    # data = Submission.objects.all().order_by("-curr_score", "-sub_time")
    sorteduser = UserProfile.objects.all().order_by("-score", "latest_sub_time")
    sub = Submission.objects.values().order_by('-user__score', 'user', 'sub_time')
    print(sub)
    try:
        user = User.objects.get(username=request.user.username)
    except User.DoesNotExist:
        user = None
    sub_list = []
    for element in sorteduser:
        sub = Submission.objects.values().filter(user_id=element.id)
        sub_list.append(sub)
        print(sub_list)
    return render(request, 'ctf/hackerboard.html', context={'sub': sub_list, 'user': sorteduser, 'curr_user': user})


'''''def first(request):
    var = calc()
    if var != 0:
        return render(request, 'ctf/.html', context={'time': var})
    else:
        return HttpResponse("time is 0:0")'''
# def leaderboard(request):
#     #data = Submission.objects.all().order_by("-curr_score", "-sub_time")
#     sorteduser = UserProfile.objects.all().order_by("-score")
# if user is not None:
#             auth.login(request, user)
#             try:
#                 userprofile = UserProfile.objects.get(user=user)
#                 userprofile.time = timer()
#                 userprofile.save()
#                 return redirect("inst")
#             except user.DoesNotExist:
#                 return render(request, 'ctf/404.html')
#
#         else:
#             return render(request, 'ctf/404.html')
