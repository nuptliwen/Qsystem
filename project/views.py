# coding=utf-8
from django.shortcuts import render_to_response, redirect, get_object_or_404, RequestContext
#from django.template.loader import get_template
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
import json
from django.contrib.sessions.models import Session
import datetime
from django.db.models import Q
from project.forms import UserForm, LoginForm, ProjectForm, changedesignForm, TestForm, Approveform, LoginForm
from project.models import department, project, project_user, public_message, project_delay, project_user_message
import models
import hashlib

from django.views.decorators.csrf import csrf_exempt

from models import project, user, project_user, project_delay, public_message, project_user_message
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from django.utils.translation import ugettext_lazy as _

#test
from django.contrib.auth.models import User
from django.contrib import auth


def register(request):
    if request.method == "POST":
        uf = UserForm(request.POST)
        if uf.is_valid(): 
            #返回注册成功页面

            #往Django user表里再插入一条数据
            username = uf.cleaned_data['username']
            password = uf.cleaned_data['password']
            realname = uf.cleaned_data['realname']
            email = username+"@ablesky.com"
            
            try:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
            except:
                uf = UserForm()
                return render_to_response('register.html',{'list':department.objects.all(), 'error':'注册的用户名已存在'},context_instance=RequestContext(request))

            user_new = uf.save();

            #登录
            uid = models.user.objects.filter(username=username)[0].id
            request.session['username'] = username
            request.session['realname'] = realname
            request.session['id'] = uid

            #Django 认证系统的登录
            user = auth.authenticate(username=username, password=password)
            auth.login(request, user)
            return HttpResponseRedirect("/personal_homepage")
    else:
        uf = UserForm()

    return render_to_response('register.html',{'list':department.objects.all()},context_instance=RequestContext(request))

def logout(request):
    try:
        session_key = request.session.session_key
        Session.objects.get(session_key=session_key).delete()
    except:
        pass
    
    return HttpResponseRedirect("/login")

def no_login(request):
    return render_to_response("nologin.html")

def no_perm(request):
    return render_to_response("noperm.html")
    
def login(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect("/personal_homepage")
    template_var={}
    
    if "username" in request.COOKIES and "password" in request.COOKIES:
        username = request.COOKIES["username"]
        password = request.COOKIES["password"]
        _userset=user.objects.filter(username__exact = username,password__exact = password)
        if _userset.count() >= 1:
            _user = _userset[0]
            request.session['username'] = _user.username
            request.session['realname'] = _user.realname
            return HttpResponseRedirect("/personal_homepage")
    
    form = LoginForm()
    if request.method == 'POST':
        form=LoginForm(request.POST.copy())
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = hashlib.md5(form.cleaned_data["password"]).hexdigest()
            isautologin = form.cleaned_data["isautologin"]
            _userset=models.user.objects.filter(username__exact = username,password__exact = password)
            if _userset.count() >= 1:
                _user = _userset[0]
                if _user.isactived:
                    request.session['username'] = _user.username
                    request.session['realname'] = _user.realname
                    request.session['id'] = _user.id
                    
                    #Django 认证系统的登录
                    try:
                        user = auth.authenticate(username=username, password=form.cleaned_data["password"])
                        auth.login(request, user)
                        
                    except:
                        template_var["error"] = _(u'您输入的帐号或密码有误，请重新输入')
                    if isautologin:
                        response.set_cookie("username", username, 3600)
                        response.set_cookie("password", password, 3600)
                        
                    response = HttpResponseRedirect("/personal_homepage")
                    return response
                else:
                    template_var["error"] = _(u'您输入的帐号未激活，请联系管理员')
            else:
                template_var["error"] = _(u'您输入的帐号或密码有误，请重新输入')
    template_var["form"]=form
    return render_to_response("login.html",template_var,context_instance=RequestContext(request))
#login


# Create your views here.

def new_project(request, pid=''):
    #没登陆的提示去登录
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/nologin")
    #编辑的得有编辑权限
    #if pid and not request.user.has_perm('project.change_project'):
     #   return HttpResponseRedirect("/noperm")
    #新建的得有新建权限
    #if not pid and not request.user.has_perm('project.add_project'):
     #   return HttpResponseRedirect("/noperm")
    form = ProjectForm()
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            priority = form.cleaned_data['priority']
            pname = form.cleaned_data['pname']
            status = form.cleaned_data['status']
            leaderid = form.cleaned_data['leader']
            leader = models.user.objects.get(id=leaderid)
            designer = form.cleaned_data['designer']
            if designer:
                designer = models.user.objects.get(id=designer)
            tester = form.cleaned_data['tester']
            if tester:
                tester = models.user.objects.get(id=tester)
            sdate = form.cleaned_data['startdate']
            pdate = form.cleaned_data['plandate']
            psdate = form.cleaned_data['psdate']
            pedate = form.cleaned_data['pedate']
            dsdate = form.cleaned_data['dsdate']
            dedate = form.cleaned_data['dedate']
            tsdate = form.cleaned_data['tsdate']
            tedate = form.cleaned_data['tedate']
            ppath = form.cleaned_data['ppath']
            dppath = form.cleaned_data['dppath']
            tppath = form.cleaned_data['tppath']
            tcpath = form.cleaned_data['tcpath']
            trpath = form.cleaned_data['trpath']
            relateduser = form.cleaned_data['relateduser']
            if pid == '':
                pro = models.project(priority=priority, project=pname, status_p=status, leader_p=leader, \
                    designer_p=designer, tester_p=tester, start_date=sdate, expect_launch_date=pdate, \
                    estimated_product_start_date=psdate, estimated_product_end_date=pedate, \
                    estimated_develop_start_date=dsdate, estimated_develop_end_date=dedate, \
                    estimated_test_start_date=tsdate, estimated_test_end_date=tedate, blueprint_p=ppath, \
                    develop_plan_p=dppath, test_plan_p=tppath, test_case_p=tcpath, test_report_p=trpath, isactived=1)
            else:
                rdate = models.project.objects.get(id=pid).real_launch_date
                pro = models.project(id=pid, priority=priority, project=pname, status_p=status, leader_p=leader, \
                    designer_p=designer, tester_p=tester, start_date=sdate, expect_launch_date=pdate, \
                    real_launch_date=rdate, estimated_product_start_date=psdate, estimated_product_end_date=pedate, \
                    estimated_develop_start_date=dsdate, estimated_develop_end_date=dedate, \
                    estimated_test_start_date=tsdate, estimated_test_end_date=tedate, blueprint_p=ppath, \
                    develop_plan_p=dppath, test_plan_p=tppath, test_case_p=tcpath, test_report_p=trpath, isactived=1)
            pro.save()
            
            #存完项目，存相关产品测试开发人员信息
            relateduser = relateduser.replace(" ", "").split(",")
            if len(relateduser):
                if pid == '':
                    pid = models.project.objects.filter(project=pname).order_by("-id")[0].id
                else:
                    models.project_user.objects.filter(project_id=pid).delete()
                for uid in relateduser:
                    if uid:
                        project_user = models.project_user(username_id=uid, project_id=pid, isactived=1)
                        project_user.save()

            #给项目负责人添加编辑项目权限
            musername = models.user.objects.get(id=leaderid).username
            User.objects.get(username=musername).user_permissions.add(26)
            if designer:
                dusername = models.user.objects.get(id=form.cleaned_data['designer']).username
                User.objects.get(username=dusername).user_permissions.add(26)
            if tester:
                tusername = models.user.objects.get(id=form.cleaned_data['tester']).username
                User.objects.get(username=tusername).user_permissions.add(26)

            #上线后发一条公告,如果表中项目ID存在,排序看isactived是否为0,如果不存在该项目ID或最小的isactived=0,则插入公告
            if status == "已上线":
                prolist = models.public_message.objects.filter(project=pid).order_by("isactived")
                try:
                    prolist[0].isactived
                except IndexError:
                    try:
                        request.session['id']
                    except KeyError:
                        return HttpResponseRedirect("/nologin")
                    else:
                        usrid = request.session['id']
                        project = models.project.objects.get(id=pid)
                        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%I:%S")
                        content = project.project + u"于"+time+u"已上线"
                        pmessage = models.public_message(project=pid, publisher=usrid, content=content, type_p="notice", publication_date=datetime.datetime.now(),isactived=False)
                        pmessage.save()
                        project.real_launch_date = datetime.datetime.now()
                        project.save()
                        print 123
                else:
                    if prolist[0].isactived != 0:
                        try:
                            request.session['id']
                        except KeyError:
                            return HttpResponseRedirect("/nologin")
                        else:
                            usrid = request.session['id']
                            print usrid
                        project = models.project.objects.get(id=pid)
                        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%I:%S")
                        content = project.project + u"于"+time+u"已上线"
                        pmessage = models.public_message(project=pid,publisher=usrid, content=content, type_p="notice", publication_date=datetime.datetime.now(),isactived=False)
                        pmessage.save()
                        project.real_launch_date = datetime.datetime.now()
                        project.save()
                        print 222
                    
            return redirect('/projectlist/')

    return render_to_response('newproject.html', {'form':form}, context_instance=RequestContext(request))
    

def project_list(request):
	
    noticess=public_message.objects.filter(type_p='notice').order_by('-id')
    count=len(noticess)
    notices=noticess[:5]
    a = 0
    if count == 0:
        a = 0
    elif count == 1:
        a = 0
    elif count == 2:
        a = 0
    elif count == 3:
        a = 0
    elif count == 4:
        a = 0
    else:
        a = len(noticess)-5    	
	

    projectlist = None
    puser=None
    project_name=""
    start_date_s=""
    end_date_s=""
    status_p=""
    leader_p=""
    project_user_list=None
    puser=project_user.objects.all()
    #projectlist = project.objects.all()
    if request.method == 'POST':
        search_form = ProjectSearchForm(request.POST)
        if search_form.is_valid():
            project_name = search_form.cleaned_data['project']
            start_date_s = search_form.cleaned_data['start_date_s']
            end_date_s = search_form.cleaned_data['end_date_s']
            status_p = search_form.cleaned_data['status_p']
            leader_p = search_form.cleaned_data['leader_p']

            projectlist = project.objects.filter().order_by("-id")
            
            if not isNone(project_name):
                projectlist = projectlist.filter(project__contains=project_name.strip()).order_by("-id")
            if not isNone(start_date_s):
                projectlist = projectlist.filter(start_date__gte=start_date_s).order_by("-id")
            if not isNone(end_date_s):
                projectlist = projectlist.filter(start_date__lte=end_date_s).order_by("-id")
            if not isNone(status_p):
                projectlist = projectlist.filter(status_p=status_p.strip()).order_by("-id")
            if not isNone(leader_p):
                #projectlist = projectlist.filter(leader_p__username__contains=leader_p.strip())
                project_user_list = project_user.objects.filter(username__realname__contains=leader_p.strip())
                projectids = []
                for p in project_user_list:
                    projectids.append(p.project.id)

                projectlist = projectlist.filter(pk__in=projectids).order_by("-id")

    else:
        projectlist = project.objects.all().order_by("-id")
        
    paginator = Paginator(projectlist, 25)
    page = request.GET.get('page')
    try:
        projectobj = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        projectobj = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        projectobj = paginator.page(paginator.num_pages)

    return render_to_response('projectlist.html',RequestContext(request, {'projectobj': projectobj,'puser':puser,'project_name':project_name,'start_date_s':start_date_s,'end_date_s':end_date_s,"status_p":status_p,"leader_p":leader_p,'notices': notices,'count':count,'a':a}))

def isNone(s):
    if s is None or (isinstance(s,basestring) and len(s.strip()) == 0):
        return True
    else:
        return False
    
def detail(request, pid):
    pro = models.project.objects.get(id=int(pid))
    user = models.user.objects.get(id = pro.leader_p_id)
    qas = models.user.objects.filter(project_user__project_id=pid, department_id=1)
    qa = {'rel': qas}
    devs = models.user.objects.filter(project_user__project_id=pid, department_id=2)
    dev= {'rel': devs}
    pds = models.user.objects.filter(project_user__project_id=pid, department_id=3)
    pd = {'rel': pds}
    related_user = {'qa':qa, 'dev': dev, 'pd': pd}
    dt_temp ={}
    dt = {}
    #处理时间为空,无法计算时间差   
    if ((pro.estimated_product_end_date!=None) & (pro.estimated_product_start_date!=None)):
        dt_temp['p']= pro.estimated_product_end_date - pro.estimated_product_start_date
        dt['ptime']= int(dt_temp['p'].days+1)
    else:
        dt['ptime']= 0
    if ((pro.estimated_develop_end_date!=None) & (pro.estimated_develop_start_date!=None)):
        dt_temp['d']= pro.estimated_develop_end_date - pro.estimated_develop_start_date
        dt['dtime']= int(dt_temp['d'].days+1)
    else:
        dt['dtime']= 0
    if ((pro.estimated_test_end_date!=None) & (pro.estimated_test_start_date!=None)):
        dt_temp['t']= pro.estimated_test_end_date - pro.estimated_test_start_date
        dt['ttime']= int(dt_temp['t'].days+1)
    else:
        dt['ttime']= 0    
    
    if ('/detail/' in request.path) :
        res = {'pro':pro, 'user':user, 'dt': dt, 'reuser': related_user}
        return render_to_response('detail.html',{'res': res})
    elif ('/editproject' in request.path):
        res = {'pro':pro, 'user':user, 'dt': dt, 'reuser': related_user, 'request': 1}
        return render_to_response('newproject.html',{'res': res})

def show_person(request):
    roles = request.GET['role']
    key = 0
    if roles == "tes":
        key = 1
    elif roles == "dev":
        key = 2
    elif roles == "pro":
        key = 3
    else:
        key = 0
    person = models.user.objects.filter(department_id=key)
    rs = []
    num = len(person)
    if num == 0:
        rrs = {"person":rs}
        rs = json.dumps(rrs)
        return HttpResponse(rs)
    for item in person:
        uid = item.id
        realname = item.realname
        dic = {'id':int(uid), 'realname':realname}
        rs.append(dic)

    rrs = {"person":rs}
    rs = json.dumps(rrs)
    return HttpResponse(rs)  
def psearch(request):
    key = request.GET['key']
    role = request.GET['role']
    ptype = 0
    if role == "tes":
        ptype = 1
    elif role == "dev":
        ptype = 2
    elif role == "pro":
        ptype = 3
    else:
        ptype = 0
    prs = models.user.objects.filter(realname__contains=key, department_id=ptype, isactived=1)
    rs = []
    if len(prs) > 0:
        for item in prs:
            dic = {'id':item.id, 'realname':item.realname}
            rs.append(dic)
        rrs = {"person":rs}
        rs = json.dumps(rrs)
    else:
        rrs = {"person":rs}
        rs = json.dumps(rrs)
    return HttpResponse(rs)

def show_headname(request):
    user = {}
    try:
        username = request.session['username']
        realname = request.session['realname']
        user['username'] = username
        user['realname'] = realname      
    except KeyError:
        user['username'] = 'GUEST'
        user['realname'] = 'GUEST'
    rs = json.dumps(user)
    return HttpResponse(rs)

#homepage部分views
def personal_homepage(request):
    try:
        request.session['username']
        projectlist = project.objects.filter()
        #print projectlist
        project_user_list = project_user.objects.filter(username__username__contains=request.session['username'])
    except KeyError:
        return HttpResponseRedirect("/nologin")          
    projectids = []
    for p in project_user_list:
        projectids.append(p.project.id)

    projectlist = projectlist.filter(pk__in=projectids)    
    result=projectlist.exclude(Q(status_p=u'已上线')| Q(status_p=u'暂停')).order_by("-id")
    result1=projectlist.exclude(~Q(status_p=u'已上线')& ~Q(status_p=u'暂停')).order_by("-id")
    puser=project_user.objects.all()
    #分页 
    paginator = Paginator(result, 1)
    page = request.GET.get('page')
    try:
        projectobj = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        projectobj = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        projectobj = paginator.page(paginator.num_pages)
    
    #userid = request.session['id']
    userid=request.session['id']
    j=0
    if request.user.has_perm('project.change_project_delay'):
        j=1
    
    i=0
    tests= project_user_message.objects.filter(userid_id=userid)
    lists=[]
    messagess=[]
    for test in tests:
        lists.append(test.messageid_id)
        messagess = public_message.objects.filter(pk__in=lists).filter(type_p = "message").order_by('-publication_date')
  
    for item in messagess:
        i=i+1 
    count=i
    messages=messagess[:4]
   
    return render_to_response('personal_homepage.html',
        {'projectobj':projectobj,'result':result,'result1':result1,'puser':puser,'messages': messages,'count':count,'j':j})

def deleteproject(request,id,url):
    delpro=get_object_or_404(project,pk=int(id))    
    delpro.delete()
    return HttpResponseRedirect(url)


def pauseproject(request,id,url):
    pausepro=get_object_or_404(project,pk=int(id))
    pausepro.status_p='暂停'
    pausepro.save()
    return HttpResponseRedirect(url)

def delayproject(request,url):
    if request.method=='POST':
        form = delayprojectForm(request.POST)
        if form.is_valid():
            delayid=form.cleaned_data['delayid']
            delay_date = form.cleaned_data['delay_date']
            delay_reason = form.cleaned_data['delay_reason']
            delpro=project.objects.get(id=delayid)
            uid=delpro.leader_p
            protitle=delpro.project
            delay_p=project_delay(application=uid,project_id=delayid,delay_to_date=delay_date,apply_date=datetime.datetime.now(),title=protitle,reason=delay_reason)
            delay_p.save()                   
    return HttpResponseRedirect(url)


def changedesign(request,url):
          
    if request.method=='POST':
        form = changedesignForm(request.POST)
        if form.is_valid():
            changeid=form.cleaned_data['changeid']
            content = form.cleaned_data['content']
            dpath = form.cleaned_data['dpath']
            chd=project.objects.get(id=changeid)
            uid=request.session['id']
            #chd.blueprint_p=dpath
            #chd.save()
            string=content+dpath
            pub_message=public_message(project=changeid,publisher=uid,content=string,type_p="message",publication_date=datetime.datetime.now(),isactived="1")
            pub_message.save()
            related_user = models.user.objects.filter(project_user__project_id=changeid)
            message=models.public_message.objects.filter(project=changeid).order_by("-id")[0]            
            for i in related_user:
                uid=i.id
                megid=message.id
                pro_u_message=project_user_message(userid_id=uid,messageid_id=megid,project_id=changeid,isactived='1')
                pro_u_message.save()           
    return HttpResponseRedirect(url)
    return render_to_response('personal_homepage.html', {'form': form})

#资源管理
def judge(request):
    try:
        if request.session['username']:
            username = request.session['username']
        Position_level = models.user.objects.get(username=\
        username).Position_level
        if Position_level == '1':
            return redirect('/show_user/')
        else:
            return redirect('/nopermit/')
    except KeyError:
        return redirect('/login/')
def nopermit(request):
    try:
        if request.session['username']:
            username = request.session['username']
            department_id = models.user.objects.get(username=\
            username).department_id
        department_id = department_id
        department = models.department.objects.get(id=\
        department_id).department
        department_list = models.department.objects.all()
        level_1_list = models.user.objects.filter(department_id=\
        department_id, Position_level="1")
        level_2_list = models.user.objects.filter(department_id=\
        department_id, Position_level="2")
        level_3_list = models.user.objects.filter(department_id=\
        department_id, Position_level="3")
        return render_to_response('nopermit.html', locals())
    except KeyError:
        return redirect('/login/')

@csrf_exempt
def show_user2(request):
    department = request.POST['department']
    if department == '请选择':
        department_id = 0
    else:
        depart = models.department.objects.all()
        departdic = {}
        for item in depart:
            departdic[item.department] = item.id
        department_id = departdic[department]
    level_1_list = models.user.objects.filter(department_id=\
    department_id, Position_level="1")
    level_2_list = models.user.objects.filter(department_id=\
    department_id, Position_level="2")
    level_3_list = models.user.objects.filter(department_id=\
    department_id, Position_level="3")
    department_list = models.department.objects.all()
    return render_to_response('nopermit.html', locals())

@csrf_exempt
def show_user(request):
    try:
        if request.session['username']:
            username = request.session['username']
            department_id = models.user.objects.get(username=\
            username).department_id
        department_id = department_id
        department = models.department.objects.get(id=\
        department_id).department
        if request.method == 'POST':
            department = request.POST['department']
            if department == '请选择':
                department_id = 0
            else:
                depart = models.department.objects.all()
                departdic = {}
                for item in depart:
                    departdic[item.department] = item.id
                department_id = departdic[department]
        else:
            department_id = department_id
        level_list = models.user.objects.filter(department_id=\
        department_id)
        level_1_list = models.user.objects.filter(department_id=\
        department_id, Position_level="1")
        level_2_list = models.user.objects.filter(department_id=\
        department_id, Position_level="2")
        level_3_list = models.user.objects.filter(department_id=\
        department_id, Position_level="3")
        department_list = models.department.objects.all()
        return render_to_response('sourcemanage.html', locals())
    except KeyError:
        return redirect('/login/')

@csrf_exempt
def Insert_user(request, id, id2):
    if request.session['username']:
        username = request.session['username']
        department_id = models.user.objects.get(username=\
        username).department_id
    department_id = department_id
    department = request.POST['department']
    if department == '请选择':
        department_id = 0
    else:
        depart = models.department.objects.all()
        departdic = {}
        for item in depart:
            departdic[item.department] = item.id
        department_id = departdic[department]
    if id == '1':
        realname = request.POST['level_1']
        user = models.user.objects.filter(department_id=\
        department_id, realname=realname).update(Position_level='1')
    elif id == '2':
        realname = request.POST['level_2a']
        user = models.user.objects.filter(department_id=department_id, \
        realname=realname).update(Position_level='2')
    elif id == '3':
        realname = request.POST['level_3a']
        user = models.user.objects.filter(department_id=department_id, \
        realname=realname).update(Position_level='3')
    elif id == '4':
        realname = request.POST['level_1']
        user = models.user.objects.filter(department_id=department_id, \
        realname=realname).update(Position_level='0')
    elif id == '5':
        user = models.user.objects.filter(department_id=department_id, \
        id=id2).update(Position_level='0')
    elif id == '6':
        user = models.user.objects.filter(department_id=department_id, \
        id=id2).update(Position_level='0')
    elif id == '7':
        realname = request.POST['level_1']
        user = models.user.objects.get(department_id=department_id, \
        realname=realname)
        user.delete()
    elif id == '8':
        user = models.user.objects.get(department_id=department_id, \
        id=id2)
        user.delete()
    elif id == '9':
        user = models.user.objects.get(department_id=department_id, \
        id=id2)
        user.delete()
    return redirect('/show_user/')


def delay(request):

    if not request.session['id']:
        return HttpResponseRedirect("/nologin")

    if not request.user.has_perm('project.change_project_delay'):
        return HttpResponseRedirect("/noperm")


    userid = request.session['id']

    delays = project_delay.objects.filter(isactived__isnull=True).order_by('apply_date')
    global  projectobj
    paginator = Paginator(delays, 20)
    page = request.GET.get('page')
    try:
        projectobj = paginator.page(page)
    except PageNotAnInteger:
        #If page is not an integer, deliver first page.
        projectobj = paginator.page(1)
    except EmptyPage:
        #If page is out of range (e.g. 9999), deliver last page of results.
        projectobj = paginator.page(paginator.num_pages)
    return render_to_response('delay.html', RequestContext(request, {'projectobj': projectobj}))

def notice(request):
    if request.method == 'POST':  # 如果是post请求
        wds = request.POST
        try:
            wd = wds['wd']
            notices = public_message.objects.filter(content__icontains=wd).filter(type_p="notice").order_by("-id")

        except Exception as e:
            notices = public_message.objects.filter(type_p="notice").order_by("-id")
    else:  # Get请求
        notices = public_message.objects.filter(type_p="notice").order_by("-id")
    global  projectobj
    paginator = Paginator(notices, 20)
    page = request.GET.get('page')
    try:
        projectobj = paginator.page(page)
    except PageNotAnInteger:
    #If page is not an integer, deliver first page.
        projectobj = paginator.page(1)
    except EmptyPage:
    #If page is out of range (e.g. 9999), deliver last page of results.
        projectobj = paginator.page(paginator.num_pages)
    return render_to_response('notice.html', RequestContext(request, {'projectobj': projectobj}))

@csrf_exempt

def historymessage(request):
    # 查询与用户相关的消息
    if request.session['id']:
        useid = request.session['id']
    tests = project_user_message.objects.filter(userid_id=useid)
    lists = []
    for test in tests:
        lists.append(test.messageid_id)
    if request.method == 'POST':  # 如果是post请求
        wds = request.POST
        try:
            wd = wds['wd']
            messages = public_message.objects.filter(pk__in=lists).filter(content__icontains=wd).filter(type_p="message").order_by('publication_date')
        except Exception as e:
            messages = public_message.objects.filter(pk__in=lists).filter(type_p="message").order_by('publication_date')
    else:  # Get请求
        messages = public_message.objects.filter(pk__in=lists).filter(type_p="message").order_by('publication_date')
    global  projectobj
    paginator = Paginator(messages, 20)
    page = request.GET.get('page')
    try:
        projectobj = paginator.page(page)
    except PageNotAnInteger:
    #If page is not an integer, deliver first page.
        projectobj = paginator.page(1)
    except EmptyPage:
    #If page is out of range (e.g. 9999), deliver last page of results.
         projectobj = paginator.page(paginator.num_pages)
    return render_to_response('historymessage.html', RequestContext(request, {'projectobj': projectobj}))


def refuse(request):
    if request.method == 'POST':

        form = TestForm(request.POST)
        if form.is_valid():
            delayid = form.cleaned_data['delayid']
            reason = form.cleaned_data['reason']
            delay = project_delay.objects.get(id=delayid)
            publisher_id = delay.application_id
            project_id = delay.project_id
            deltitle = delay.title
            string = deltitle+u"申请延期被拒绝，理由"+reason
            #delpro=project.objects.get(id=delayid)
            if request.session['id']:

                useid = request.session['id']
                pub_message = public_message(project=project_id, publisher=useid, content=string, \
                    type_p="message", publication_date=datetime.datetime.now(), delay_status="已拒绝", isactived="1")
            #delay.reason = reason

                delay.isactived = 0
                delay.save()
                pub_message.save()
                related_user = models.user.objects.filter(project_user__project_id=project_id)
                message = models.public_message.objects.filter(project=project_id).order_by("-id")[0]
            for i in related_user:
                uid = i.id
                megid = message.id
                pro_u_message = project_user_message(userid_id=uid, messageid_id=megid, project_id=project_id, isactived='1')
                pro_u_message.save()
    delays = project_delay.objects.filter(isactived=True)
    return HttpResponseRedirect('/delay/')


def approve(request):
    if request.method == 'POST':
        form = Approveform(request.POST)
        if form.is_valid():
            delayid1 = form.cleaned_data['delayid1']
            delay = project_delay.objects.get(id=delayid1)
            publisher_id = delay.application_id
            project_id = delay.project_id
            deltitle = delay.title
            aa = delay.delay_to_date
            del_to_date = str(aa)
            string = deltitle + u"延期至：" + del_to_date
            #delpro=project_delay.objects.get(id=delayid1)
        if request.session['id']:
            useid = request.session['id']
            pub_message = public_message(project=project_id, publisher=useid, content=string, type_p="notice", \
                publication_date=datetime.datetime.now(), delay_status="已批准", isactived="1")
            #delay.reason = reason

            delay.isactived = 1
            delay.save()
            pub_message.save()

    raw_sql = 'select * from project_project_delay where isactived is null'
    delays = project_delay.objects.raw(raw_sql)
    return HttpResponseRedirect('/delay/')


def deletehistory(request):
    if request.session['id']:
        useid = request.session['id']
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            messageid = form.cleaned_data['messageid']
            usermessage = project_user_message.objects.get(userid_id=useid, messageid_id=messageid)
            usermessage.delete();
    tests = project_user_message.objects.filter(userid_id=useid)
    lists = []
    for test in tests:
        lists.append(test.messageid_id)
    messages = public_message.objects.filter(pk__in=lists).filter(type_p="message").order_by('publication_date')
    return HttpResponseRedirect('/historymessage/')

def deletenotice(request):
    if request.session['id']:
        useid = request.session['id']
    if request.method == 'POST':
        form = NoticeForm(request.POST)
        if form.is_valid():
            noticeid = form.cleaned_data['noticeid']
            usernotice = project_user_message.objects.get(userid_id=useid, messageid_id=noticeid)
            usernotice.delete();
    tests = project_user_message.objects.filter(userid_id=useid)
    lists = []
    for test in tests:
        lists.append(test.messageid_id)
    notices = public_message.objects.filter(pk__in=lists).filter(type_p="notice").order_by('publication_date')
    return HttpResponseRedirect('/notice/')

