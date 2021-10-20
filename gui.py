import os
import pickle
import sys
import time
import dlib
import cv2
import face_recognition
from os import listdir
from os.path import isfile, join
import threading
from PyQt5 import uic, QtCore, QtGui, QtWidgets
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QDialog, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, \
    QStatusBar, QToolBar, QAction, QComboBox, QFileDialog, QListWidget, QTextEdit, QInputDialog
from PyQt5.QtCore import QCoreApplication, pyqtSignal, pyqtSlot, Qt, QThread, QTimer
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *
from PyQt5.QtGui import QPixmap, QImage
import pymongo
import bcrypt
import numpy as np
import img


data_path = 'users/'  # 사용자 파일이 저장될 기본 경로
Login = False
Admin = False
DB = pickle.loads(open("../pyqt_final/DBkey", "rb").read())     # 데이터베이스 비밀번호를 담고 있는 피클 파일을 연다
client = pymongo.MongoClient(DB)
user_name = 'none'
user = 'none'


def load_data(path):  # 리스트 파일 로드 함수
    # 폴더가 있을때 파일이 없는경우 onlyfiles 폴더를 만들지 못함
    global onlyfiles
    try:  # 폴더가 있는경우
        onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]  # users 폴더에 존재하는 모든 파일을 배열로 저장한다
    except OSError:  # 폴더 없는 경우 에러 메시지
        onlyfiles = []


def createFolder(directory):  # 폴더 생성 함수
    if not os.path.exists(directory):  # 해당 디렉토리가
        os.makedirs(directory)  # 디렉토리를 생성한다


def open_folder():
    # users 폴더 없을때 생성할수 있게 수정 완료
    path = os.path.realpath('users/')
    createFolder(path)
    os.startfile(path)


def gotohome():
    home = Home_Screen()
    widget.addWidget(home)
    widget.setCurrentIndex(widget.currentIndex() + 1)


def loginstate():
    global Login
    Login = True


def adminstate():
    global Admin
    global Login
    Admin = True
    Login = True


def logoutstate():
    global Login
    global Admin
    Login = False
    Admin = False
    gotohome()


class Home_Screen(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("ui/home.ui", self)
        self.setFixedHeight(600)
        self.setFixedWidth(400)
        self.pushButton_2.clicked.connect(self.gotolocal)
        self.pushButton_3.clicked.connect(QCoreApplication.instance().quit)  # quit 버튼 (종료)
        self.pushButton.clicked.connect(self.gotologin)

    def gotologin(self):
        login = Login_Screen()
        widget.addWidget(login)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotolocal(self):
        local = Local_Menu()
        widget.addWidget(local)
        widget.setCurrentIndex(widget.currentIndex() + 1)


class Local_Menu(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("ui/localmenu.ui", self)
        self.setFixedHeight(600)
        self.setFixedWidth(400)
        self.backButton.clicked.connect(gotohome)
        self.detectButton.clicked.connect(self.gotodetect)
        self.userButton.clicked.connect(self.gotoedit)
        self.pushButton_4.clicked.connect(self.gotologin)
        self.pushButton_3.clicked.connect(QCoreApplication.instance().quit)  # quit 버튼 (종료)

    def gotologin(self):
        login = Login_Screen()
        widget.addWidget(login)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotodetect(self):
        detect = Detect('guest')
        widget.addWidget(detect)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotoedit(self):
        edit = User_Edit()
        widget.addWidget(edit)
        widget.setCurrentIndex(widget.currentIndex() + 1)


class User_Edit(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("ui/useredit.ui", self)
        self.setFixedHeight(600)
        self.setFixedWidth(400)
        self.Uplist()
        self.label.setAlignment(Qt.AlignCenter)
        self.backButton.clicked.connect(self.gotolocal)
        self.pushButton_3.clicked.connect(QCoreApplication.instance().quit)  # quit 버튼 (종료)
        self.pushButton_2.clicked.connect(self.Deleteuser)
        self.pushButton_4.clicked.connect(self.rename)
        self.pushButton.clicked.connect(self.Adduser)

    def rename(self):
        if self.listWidget.currentItem():
            encodings = []
            change = []
            select = self.listWidget.currentItem().text()
            print(select)
            cam = Get_Name()
            cam.exec_()
            print(user)
            file = 'users/' + select
            new_file = 'users/' + user
            print(new_file)
            os.rename(file, new_file)
            try:
                data = pickle.loads(open(new_file, "rb").read())
            except OSError:
                print('can\'t found ' + user)

            for i in data["encodings"]:
                encodings.append(i)
                change.append(user)

            change_file = {"encodings": encodings, "names": change}

            files = open(new_file, 'wb')
            files.write(pickle.dumps(change_file))
            files.close()

            self.Uplist()
        else:
            QMessageBox.about(self, "Error", "이름을 변경할 사용자를 선택하세요.")

    def gotolocal(self):
        local = Local_Menu()
        widget.addWidget(local)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def Uplist(self):  # 리스트에 사용자를 추가하거나 삭제할시 리스트를 갱신해주는 함수
        self.listWidget.clear()
        load_data(data_path)
        for data in onlyfiles:
            self.listWidget.addItem(data)

    def Adduser(self):
        add = Add_User()
        widget.addWidget(add)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        self.Uplist()

    def Deleteuser(self):  # 사용자를 삭제하는 함수

        if self.listWidget.currentItem():

            select = self.listWidget.currentItem().text()
            print(select)
            file = 'users/' + select

            if os.path.isfile(file):  # 선택한 파일이 존재할경우에
                response = QMessageBox.question(self, 'Message', 'Are you sure to delete',
                                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                print(response)
                if response == QMessageBox.Yes:
                    os.remove(file)  # 파일을 삭제한다
                    self.Uplist()
                    QMessageBox.about(self, "INFO", "파일" + select + "의 삭제가 완료 되었습니다")  # 삭제완료 메세지 박스로 알려준다
                else:
                    QMessageBox.about(self, "CANCEL", "파일" + select + "의 삭제를 취소하였습니다")
            else:
                QMessageBox.about(self, "Error",
                                            "삭제할 파일이 존재하지 않습니다다")  # 파일이 존재하지 않을 경우에 메세지박스로 알려준다(정상적인 상황에서 발생할수 없는 오류)
        else:

            QMessageBox.about(self, "Error", "삭제할 사용자를 선택하세요.")


class Add_User(QMainWindow):  # 사용자 추가 방식 고르는 페이지
    def __init__(self):
        super().__init__()
        loadUi("ui/adduser.ui", self)
        self.setFixedHeight(600)
        self.setFixedWidth(400)
        self.detectButton.clicked.connect(self.getname)
        self.backButton.clicked.connect(self.gotoedit)
        self.pushButton_4.clicked.connect(self.runimage)
        self.pushButton_3.clicked.connect(QCoreApplication.instance().quit)  # quit 버튼 (종료)

    def getname(self):
        cam = Get_Name()
        cam.exec_()
        print(user)
        if user != 'none':
            addcam = Add_Cam(user)
            addcam.exec_()

    def gotoedit(self):
        edit = User_Edit()
        widget.addWidget(edit)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def dest_folder(self):  # 찾아보기 버튼  파일경로읽어오기
        files = QtWidgets.QFileDialog.getExistingDirectory(self, 'select image directory')

        global select_folder  # 선택 파일 경로
        select_folder = files + '/'
        print(select_folder)

    def runimage(self):
        cam = Get_Name()
        cam.exec_()

        if user != 'none':
            self.dest_folder()
            if select_folder != '/':
                knownEncodings = []
                knownNames = []

                onlyfile = [f for f in listdir(select_folder) if isfile(join(select_folder, f))]
                for i, files in enumerate(onlyfile):
                    filename = select_folder + onlyfile[i]
                    print(filename)
                    print(onlyfile[i])
                    images = cv2.imread(filename)
                    assert images is not None, ' can\'t open file as img'

                    rgb = cv2.cvtColor(images, cv2.COLOR_BGR2RGB)
                    boxes = face_recognition.face_locations(rgb, model='CNN')
                    encodings = face_recognition.face_encodings(rgb, boxes)

                    if not boxes:  # 이미지에 얼굴이 없을겨우 종료
                        print("인식 실패")
                        QMessageBox.about(self, "Error", "식별이 안되는 이미지가 있습니다.")
                        return 0

                    for encoding in encodings:
                        knownEncodings.append(encoding)
                        knownNames.append(user)
                        print(encoding)

                data = {"encodings": knownEncodings, "names": knownNames}
                createFolder('./users')
                f = open(data_path + user, 'wb')
                print(data)
                f.write(pickle.dumps(data))
                f.close()
                QMessageBox.about(self, "INFO", "사용자 등록 완료.")


class Get_Name(QDialog):
    def __init__(self):
        super().__init__()
        loadUi("ui/getname.ui", self)
        self.setFixedHeight(300)
        self.setFixedHeight(200)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.pushButton_2.clicked.connect(self.close)
        self.pushButton.clicked.connect(self.getback)

    def getback(self):
        global user
        user = self.lineEdit.text()
        print(user)
        self.close()


class Add_Cam(QDialog):
    def __init__(self, user):
        super().__init__()
        loadUi("ui/local.ui", self)
        self.user = user
        self.setFixedHeight(700)
        self.setFixedWidth(800)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.backButton.clicked.connect(self.stop)
        self.start()

    def run(self):
        knownEncodings = []
        knownNames = []
        global check
        check = False
        global running
        cap = cv2.VideoCapture(0)
        count = 0
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.label.resize(width, height)
        while running:
            ret, img = cap.read()
            if ret:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                boxes = face_recognition.face_locations(img, model='CNN')
                encodings = face_recognition.face_encodings(img, boxes)
                for encoding in encodings:
                    check = True
                    print(self.user, encoding)
                    knownEncodings.append(encoding)
                    knownNames.append(self.user)
                    count += 1

                if check is False:
                    cv2.putText(img, "Face not Found", (0, 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    pass

                for ((top, right, bottom, left), name) in zip(boxes, knownNames):
                    # rescale the face coordinates

                    color = (255, 255, 0)
                    cv2.rectangle(img, (left, top), (right, bottom), color, 2)

                    y = top - 15 if top - 15 > 15 else top + 15

                    ename = user + str(count) + '%'
                    if count == 100:
                        ename = "complete"
                    cv2.putText(img, ename, (left, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)

                h, w, c = img.shape
                print(h, w, c)
                qImg = QtGui.QImage(img.data, w, h, w * c, QtGui.QImage.Format_RGB888)
                pixmap = QtGui.QPixmap.fromImage(qImg)
                self.label.setPixmap(pixmap)
                check = False

                if count == 100:
                    print("collecting samples complete")
                    break
        data = {"encodings": knownEncodings, "names": knownNames}
        createFolder('./users')
        f = open('users/' + self.user, "ab")
        f.write(pickle.dumps(data))
        f.close()

        cap.release()
        print("Thread end.")
        self.stop()

    def stop(self):
        global running
        running = False
        print("stoped..")
        self.close()

    def start(self):
        global running
        running = True
        th = threading.Thread(target=self.run)
        th.start()
        print("started..")


class Choose_One(QMainWindow):
    def __init__(self, user, level):
        super().__init__()
        loadUi("ui/choose.ui", self)
        self.user = user
        self.level = level
        self.setFixedHeight(600)
        self.setFixedWidth(400)
        self.detectButton.clicked.connect(self.webone)
        self.backButton.clicked.connect(self.goback)
        self.userButton.clicked.connect(self.imgone)
        self.pushButton_6.clicked.connect(self.videone)
        self.pushButton_5.clicked.connect(QCoreApplication.instance().quit)

    def goback(self):
        if self.level == 'admin':
            admin = Detect('admin')
            widget.addWidget(admin)
            widget.setCurrentIndex(widget.currentIndex() + 1)
        elif self.level == 'member':
            member = Detect('member')
            widget.addWidget(member)
            widget.setCurrentIndex(widget.currentIndex() + 1)
        else:
            back = Detect('guest')
            widget.addWidget(back)
            widget.setCurrentIndex(widget.currentIndex() + 1)

    def webone(self):
        cam = Camera(self.user, 0)
        cam.camstart()
        cam.exec_()

    def imgone(self):
        image_file = QtWidgets.QFileDialog.getOpenFileName(self, 'select image')
        img = image_file[0]
        if img:
            cam = Camera(self.user, img)
            cam.imgstart()
            cam.exec_()
        else:
            pass

    def videone(self):
        video_file = QtWidgets.QFileDialog.getOpenFileName(self, 'select image')
        video = video_file[0]
        if video:
            cam = Camera(self.user, video)
            cam.videostart()
            cam.exec()


class Choose_All(QMainWindow):
    def __init__(self, level):
        super().__init__()
        loadUi("ui/choose.ui", self)
        self.setFixedHeight(600)
        self.setFixedWidth(400)
        self.level = level
        self.detectButton.clicked.connect(self.camall)
        self.backButton.clicked.connect(self.goback)
        self.userButton.clicked.connect(self.imgall)
        self.pushButton_6.clicked.connect(self.videall)
        self.pushButton_5.clicked.connect(QCoreApplication.instance().quit)

    def camall(self):
        find = FindAll(1)
        find.camstart()
        find.exec_()

    def goback(self):
        if self.level == 'admin':
            admin = Detect('admin')
            widget.addWidget(admin)
            widget.setCurrentIndex(widget.currentIndex() + 1)
        elif self.level == 'member':
            member = Detect('member')
            widget.addWidget(member)
            widget.setCurrentIndex(widget.currentIndex() + 1)
        else:
            back = Detect('guest')
            widget.addWidget(back)
            widget.setCurrentIndex(widget.currentIndex() + 1)

    def imgall(self):
        image_file = QtWidgets.QFileDialog.getOpenFileName(self, 'select image')
        img = image_file[0]
        if img:
            cam = FindAll(img)
            cam.imgstart()
            cam.exec_()
        else:
            pass

    def videall(self):
        video_file = QtWidgets.QFileDialog.getOpenFileName(self, 'select image')
        video = video_file[0]
        if video:
            cam = FindAll(video)
            cam.videostart()
            cam.exec()


class Detect(QMainWindow):  
    def __init__(self, level):
        super().__init__()
        loadUi("ui/listest.ui", self)
        self.level = level
        self.setFixedHeight(600)
        self.setFixedWidth(400)
        self.AddItem()
        self.label.setAlignment(Qt.AlignCenter)
        self.backButton.clicked.connect(self.back)
        self.pushButton.clicked.connect(self.findone)
        self.pushButton_3.clicked.connect(QCoreApplication.instance().quit)  # quit 버튼 (종료)
        self.pushButton_2.clicked.connect(self.findall)

    def back(self):
        if self.level == 'admin':
            admin = Admin_Page()
            widget.addWidget(admin)
            widget.setCurrentIndex(widget.currentIndex() + 1)
        elif self.level == 'member':
            member = Member_Page()
            widget.addWidget(member)
            widget.setCurrentIndex(widget.currentIndex() + 1)
        else:
            back = Local_Menu()
            widget.addWidget(back)
            widget.setCurrentIndex(widget.currentIndex() + 1)

    def AddItem(self):
        self.listWidget.clear()
        load_data(data_path)
        for data in onlyfiles:
            self.listWidget.addItem(data)

    def findall(self):
        all = Choose_All(self.level)
        widget.addWidget(all)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def findone(self):

        if self.listWidget.currentItem():
            user = self.listWidget.currentItem().text()
            one = Choose_One(user, self.level)
            widget.addWidget(one)
            widget.setCurrentIndex(widget.currentIndex() + 1)

        else:
            QMessageBox.about(self, "Error", "탐색할 사용자를 선택하세요.")


class FindAll(QDialog):     # 사용자 전체
    def __init__(self, url):
        super().__init__()
        loadUi("ui/local.ui", self)
        self.setFixedHeight(700)
        self.setFixedHeight(800)
        self.url = url
        self.scaler = 0.5
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.backButton.clicked.connect(self.stop)

    def webcam(self):
        self.run_all()

    def image(self):
        img = cv2.imread(self.url)
        self.img_all(img)

    def video(self):
        video = cv2.VideoCapture(self.url)
        self.video_all(video)

    def run_all(self):
        knownEncodings = []
        knownNames = []

        load_data(data_path)  # 리스트에 들어가 파일이 있는 폴더를 스캔해준다
        for i in onlyfiles:  # 리스트에 존재하는 파일 순서대로 입력
            u_data = pickle.loads(open('users/' + i, "rb").read())
            for encoding in u_data["encodings"]:
                knownEncodings.append(encoding)
                knownNames.append(i)

        data = {"encodings": knownEncodings, "names": knownNames}
        global running
        cap = cv2.VideoCapture(0)
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.label.resize(width, height)
        while running:
            ret, img = cap.read()
            if ret:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                boxes = face_recognition.face_locations(img, model='CNN')
                encodings = face_recognition.face_encodings(img, boxes)
                names = []
                for encoding in encodings:
                    matches = face_recognition.compare_faces(data["encodings"], encoding, tolerance=0.35)
                    name = 'unknown'

                    if True in matches:
                        matchesIndxs = []
                        for (i, b) in enumerate(matches):
                            if b:
                                matchesIndxs.append(i)

                        counts = {}

                        for items in matchesIndxs:
                            name = data['names'][items]
                            counts[name] = counts.get(name, 0) + 1

                        for items in matchesIndxs:
                            counts[data['names'][items]] = counts.get(data['names'][items]) + 1
                        name = max(counts, key=counts.get)
                        print(counts)
                    names.append(name)

                for ((top, right, bottom, left), name) in zip(boxes, names):
                    # rescale the face coordinates

                    color = (255, 255, 0)
                    if name == 'unknown':
                        color = (255, 255, 255)
                        # draw the predicted face name on the image
                    cv2.rectangle(img, (left, top), (right, bottom),
                                  color, 2)
                    y = top - 15 if top - 15 > 15 else top + 15
                    cv2.putText(img, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
                                0.75, color, 2)

                h, w, c = img.shape
                print(h, w, c)
                qImg = QtGui.QImage(img.data, w, h, w * c, QtGui.QImage.Format_RGB888)
                pixmap = QtGui.QPixmap.fromImage(qImg)
                self.label.setPixmap(pixmap)
            else:
                QMessageBox.about(self, "Error", "Cannot read frame.")
                print("cannot read frame.")
                break
        cap.release()
        print("Thread end.")

    def video_all(self, cap):
        knownEncodings = []
        knownNames = []

        load_data(data_path)  # 리스트에 들어가 파일이 있는 폴더를 스캔해준다
        for i in onlyfiles:  # 리스트에 존재하는 파일 순서대로 입력
            u_data = pickle.loads(open('users/' + i, "rb").read())
            for encoding in u_data["encodings"]:
                knownEncodings.append(encoding)
                knownNames.append(i)

        data = {"encodings": knownEncodings, "names": knownNames}

        global running

        while running:
            ret, image = cap.read()
            if ret:

                img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, (int(img.shape[1] * self.scaler), int(img.shape[0] * self.scaler)))

                boxes = face_recognition.face_locations(img, model='CNN')
                encodings = face_recognition.face_encodings(img, boxes)
                names = []
                for encoding in encodings:
                    matches = face_recognition.compare_faces(data["encodings"], encoding, tolerance=0.35)
                    name = 'unknown'

                    if True in matches:
                        matchesIndxs = []
                        for (i, b) in enumerate(matches):
                            if b:
                                matchesIndxs.append(i)

                        counts = {}

                        for items in matchesIndxs:
                            name = data['names'][items]
                            counts[name] = counts.get(name, 0) + 1

                        for items in matchesIndxs:
                            counts[data['names'][items]] = counts.get(data['names'][items]) + 1
                        name = max(counts, key=counts.get)
                        print(counts)
                    names.append(name)

                for ((top, right, bottom, left), name) in zip(boxes, names):

                    color = (255, 255, 0)
                    if name == 'unknown':
                        color = (255, 255, 255)
                        # draw the predicted face name on the image
                    cv2.rectangle(img, (left, top), (right, bottom),
                                  color, 2)
                    y = top - 15 if top - 15 > 15 else top + 15
                    cv2.putText(img, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
                                0.75, color, 2)

                h, w, c = img.shape
                self.label.resize(w, h)
                print(h, w, c)
                qImg = QtGui.QImage(img.data, w, h, w * c, QtGui.QImage.Format_RGB888)
                pixmap = QtGui.QPixmap.fromImage(qImg)
                self.label.setPixmap(pixmap)
            else:
                QMessageBox.about(self, "Error", "Cannot read frame.")
                print("cannot read frame.")
                break
        cap.release()
        print("Thread end.")

    def img_all(self, img):
        knownEncodings = []
        knownNames = []

        load_data(data_path)  # 리스트에 들어가 파일이 있는 폴더를 스캔해준다
        for i in onlyfiles:  # 리스트에 존재하는 파일 순서대로 입력
            u_data = pickle.loads(open('users/' + i, "rb").read())
            for encoding in u_data["encodings"]:
                knownEncodings.append(encoding)
                knownNames.append(i)

        data = {"encodings": knownEncodings, "names": knownNames}

        img = cv2.resize(img, (int(img.shape[1] * self.scaler), int(img.shape[0] * self.scaler)))

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(img, model='CNN')
        encodings = face_recognition.face_encodings(img, boxes)
        names = []
        for encoding in encodings:
            matches = face_recognition.compare_faces(data["encodings"], encoding, tolerance=0.35)
            name = 'unknown'

            if True in matches:
                matchesIndxs = []
                for (i, b) in enumerate(matches):
                    if b:
                        matchesIndxs.append(i)

                counts = {}

                for items in matchesIndxs:
                    name = data['names'][items]
                    counts[name] = counts.get(name, 0) + 1

                for items in matchesIndxs:
                    counts[data['names'][items]] = counts.get(data['names'][items]) + 1
                name = max(counts, key=counts.get)
                print(counts)
            names.append(name)

        for ((top, right, bottom, left), name) in zip(boxes, names):
            # rescale the face coordinates

            color = (255, 255, 0)
            if name == 'unknown':
                color = (255, 255, 255)
                # draw the predicted face name on the image
            cv2.rectangle(img, (left, top), (right, bottom),
                          color, 2)
            y = top - 15 if top - 15 > 15 else top + 15
            cv2.putText(img, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.75, color, 2)

        h, w, c = img.shape
        print(h, w, c)
        qImg = QtGui.QImage(img.data, w, h, w * c, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qImg)
        self.label.setPixmap(pixmap)

    def stop(self):
        global running
        running = False
        print("stoped..")
        self.close()

    def camstart(self):
        global running
        running = True
        th = threading.Thread(target=self.webcam)
        th.start()
        print("started..")

    def imgstart(self):
        global running
        running = True
        th = threading.Thread(target=self.image)
        th.start()
        print("started..")

    def videostart(self):
        global running
        running = True
        th = threading.Thread(target=self.video)
        th.start()
        print("started..")


class Camera(QDialog):
    def __init__(self, user, url):
        super().__init__()
        loadUi("ui/local.ui", self)
        self.user = user
        self.url = url
        self.scaler = 0.5
        self.setFixedHeight(700)
        self.setFixedWidth(800)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.backButton.clicked.connect(self.stop)

    def __del__(self):
        self.stop()

    def webcam(self):
        cap = cv2.VideoCapture(0)
        self.run(cap)

    def image(self):
        img = cv2.imread(self.url)
        self.img_run(img)

    def video(self):
        video = cv2.VideoCapture(self.url)
        self.video_run(video)

    def run(self, cap):
        knownEncodings = []
        knownNames = []

        try:
            data = pickle.loads(open('users/' + self.user, "rb").read())
        except OSError:
            print('can\'t found ' + self.user)

        for encoding in data["encodings"]:
            knownEncodings.append(encoding)
            knownNames.append(self.user)

        data = {"encodings": knownEncodings, "names": knownNames}
        global running
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.label.resize(width, height)
        while running:
            ret, img = cap.read()
            if ret:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                boxes = face_recognition.face_locations(img, model='CNN')
                encodings = face_recognition.face_encodings(img, boxes)
                names = []
                for encoding in encodings:
                    matches = face_recognition.compare_faces(data["encodings"], encoding, tolerance=0.35)
                    name = 'unknown'

                    if True in matches:
                        matchesIndxs = []
                        for (i, b) in enumerate(matches):
                            if b:
                                matchesIndxs.append(i)

                        counts = {}

                        for items in matchesIndxs:
                            name = data['names'][items]
                            counts[name] = counts.get(name, 0) + 1

                        for items in matchesIndxs:
                            counts[data['names'][items]] = counts.get(data['names'][items]) + 1
                        name = max(counts, key=counts.get)
                        print(counts)
                    names.append(name)

                for ((top, right, bottom, left), name) in zip(boxes, names):
                    # rescale the face coordinates

                    color = (255, 255, 0)
                    if name == 'unknown':
                        color = (255, 255, 255)
                        # draw the predicted face name on the image
                    cv2.rectangle(img, (left, top), (right, bottom),
                                  color, 2)
                    y = top - 15 if top - 15 > 15 else top + 15
                    cv2.putText(img, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
                                0.75, color, 2)

                h, w, c = img.shape
                print(h, w, c)
                qImg = QtGui.QImage(img.data, w, h, w * c, QtGui.QImage.Format_RGB888)
                pixmap = QtGui.QPixmap.fromImage(qImg)
                self.label.setPixmap(pixmap)
            else:
                QMessageBox.about(self, "Error", "Cannot read frame.")
                print("cannot read frame.")
                break
        cap.release()
        print("Thread end.")

    def video_run(self, cap):
        knownEncodings = []
        knownNames = []

        try:
            data = pickle.loads(open('users/' + self.user, "rb").read())
        except OSError:
            print('can\'t found ' + self.user)

        for encoding in data["encodings"]:
            knownEncodings.append(encoding)
            knownNames.append(self.user)

        data = {"encodings": knownEncodings, "names": knownNames}

        global running

        while running:
            ret, image = cap.read()
            if ret:

                img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, (int(img.shape[1] * self.scaler), int(img.shape[0] * self.scaler)))

                boxes = face_recognition.face_locations(img, model='CNN')
                encodings = face_recognition.face_encodings(img, boxes)
                names = []
                for encoding in encodings:
                    matches = face_recognition.compare_faces(data["encodings"], encoding, tolerance=0.35)
                    name = 'unknown'

                    if True in matches:
                        matchesIndxs = []
                        for (i, b) in enumerate(matches):
                            if b:
                                matchesIndxs.append(i)

                        counts = {}

                        for items in matchesIndxs:
                            name = data['names'][items]
                            counts[name] = counts.get(name, 0) + 1

                        for items in matchesIndxs:
                            counts[data['names'][items]] = counts.get(data['names'][items]) + 1
                        name = max(counts, key=counts.get)
                        print(counts)
                    names.append(name)

                for ((top, right, bottom, left), name) in zip(boxes, names):

                    color = (255, 255, 0)
                    if name == 'unknown':
                        color = (255, 255, 255)
                        # draw the predicted face name on the image
                    cv2.rectangle(img, (left, top), (right, bottom),
                                  color, 2)
                    y = top - 15 if top - 15 > 15 else top + 15
                    cv2.putText(img, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
                                0.75, color, 2)

                h, w, c = img.shape
                self.label.resize(w, h)
                print(h, w, c)
                qImg = QtGui.QImage(img.data, w, h, w * c, QtGui.QImage.Format_RGB888)
                pixmap = QtGui.QPixmap.fromImage(qImg)
                self.label.setPixmap(pixmap)
            else:
                QMessageBox.about(self, "Error", "Cannot read frame.")
                print("cannot read frame.")
                break
        cap.release()
        print("Thread end.")

    def img_run(self, img):
        knownEncodings = []
        knownNames = []

        try:
            data = pickle.loads(open('users/' + self.user, "rb").read())
        except OSError:
            print('can\'t found ' + self.user)

        for encoding in data["encodings"]:
            knownEncodings.append(encoding)
            knownNames.append(self.user)

        data = {"encodings": knownEncodings, "names": knownNames}

        img = cv2.resize(img, (int(img.shape[1] * self.scaler), int(img.shape[0] * self.scaler)))

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(img, model='CNN')
        encodings = face_recognition.face_encodings(img, boxes)
        names = []
        for encoding in encodings:
            matches = face_recognition.compare_faces(data["encodings"], encoding, tolerance=0.35)
            name = 'unknown'

            if True in matches:
                matchesIndxs = []
                for (i, b) in enumerate(matches):
                    if b:
                        matchesIndxs.append(i)

                counts = {}

                for items in matchesIndxs:
                    name = data['names'][items]
                    counts[name] = counts.get(name, 0) + 1

                for items in matchesIndxs:
                    counts[data['names'][items]] = counts.get(data['names'][items]) + 1
                name = max(counts, key=counts.get)
                print(counts)
            names.append(name)

        for ((top, right, bottom, left), name) in zip(boxes, names):
            # rescale the face coordinates

            color = (255, 255, 0)
            if name == 'unknown':
                color = (255, 255, 255)
                # draw the predicted face name on the image
            cv2.rectangle(img, (left, top), (right, bottom),
                          color, 2)
            y = top - 15 if top - 15 > 15 else top + 15
            cv2.putText(img, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.75, color, 2)

        h, w, c = img.shape
        print(h, w, c)
        qImg = QtGui.QImage(img.data, w, h, w * c, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qImg)
        self.label.setPixmap(pixmap)

    def stop(self):
        global running
        running = False
        print("stoped..")
        self.close()

    def camstart(self):
        global running
        running = True
        th = threading.Thread(target=self.webcam)
        th.start()
        print("started..")

    def imgstart(self):
        global running
        running = True
        th = threading.Thread(target=self.image)
        th.start()
        print("started..")

    def videostart(self):
        global running
        running = True
        th = threading.Thread(target=self.video)
        th.start()
        print("started..")


class Login_Screen(QMainWindow):
    def __init__(self):
        super(Login_Screen, self).__init__()
        loadUi("ui/login.ui", self)
        self.setFixedHeight(600)
        self.setFixedWidth(400)
        self.pushButton_2.clicked.connect(self.gotoregister)
        self.pushButton_3.clicked.connect(QCoreApplication.instance().quit)  # quit 버튼 (종료)
        self.pushButton.clicked.connect(self.btnClick)
        self.backButton.clicked.connect(gotohome)

    def gotoregister(self):
        reg = Reg_Screen()
        widget.addWidget(reg)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotomember(self):
        mbr = Member_Page()
        widget.addWidget(mbr)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotoadmin(self):
        admin = Admin_Page()
        widget.addWidget(admin)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def btnClick(self):
        if self.lineEdit.text() and self.lineEdit_2.text():

            global user_name
            db = client["member"]
            collection = db["member"]
            print(self.lineEdit.text())
            Id = self.lineEdit.text()
            print(Id)
            Pass = self.lineEdit_2.text()
            print(Pass)
            user_name = Id
            a = collection.find_one({"name": Id})
            if a:
                pw = a["password"]
                pw = pw.encode("utf-8")
                pw_check = bcrypt.checkpw(Pass.encode("utf-8"), pw)  # 입력값과 해쉬값이 동일한지 확인
                admin_check = a['approved']  # 관리자가 승인했는지체크 bool
                admin = a['admin']

                if pw_check:
                    if admin:
                        print("관리자")
                        QMessageBox.about(self, "Admin", "관리자로 로그인되었습니다")
                        adminstate()
                        self.gotoadmin()

                    elif admin_check:
                        print('로그인')
                        QMessageBox.about(self, "Success", "로그인되었습니다")
                        loginstate()
                        self.gotomember()
                    else:
                        print('승인안됨')
                        QMessageBox.about(self, "Warning", "관리자 승인이 되지 않은 사용자입니다")

                else:
                    print("확인요망")
                    QMessageBox.about(self, "Warning", "PassWord를 확인해주세요")

            else:
                print("check")
                QMessageBox.about(self, "Warning", "Id를 확인해주세요.")


        else:
            QMessageBox.about(self, "Error", "Id와 PassWord를 입력해주세요.")


class Reg_Screen(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("ui/register.ui", self)
        self.setFixedHeight(600)
        self.setFixedWidth(400)
        self.backButton.clicked.connect(self.gotologin)
        self.pushButton.clicked.connect(self.register)
        self.pushButton_2.clicked.connect(self.checker)
        self.pushButton_3.clicked.connect(QCoreApplication.instance().quit)  # quit 버튼 (종료)

    def gotologin(self):
        login = Login_Screen()
        widget.addWidget(login)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def checker(self):
        if self.lineEdit.text():
            db = client["member"]
            collection = db["member"]
            ID = self.lineEdit.text()
            a = collection.find_one({"name": ID})
            if a:
                QMessageBox.about(self, "Warning", "이미 존재하는 아이디 입니다.")
            else:
                QMessageBox.about(self, "INFO", "사용가능한 아이디 입니다.")
                self.pushButton.setEnabled(True)
                self.lineEdit.setDisabled(True)             # 아이디 검사 되면 못바꾸게 잠구기

        else:
            QMessageBox.about(self, "Warning", "아이디를 입력해주세요.")

    def register(self):
        if self.lineEdit.text() and self.lineEdit_2.text():
            db = client["member"]
            collection = db["member"]
            ID = self.lineEdit.text()
            Pass = self.lineEdit_2.text()
            print(type(ID))
            print(type(Pass))
            a = collection.find_one({"name": ID})

            if a:
                QMessageBox.about(self, "Warning", "이미 존재하는 아이디 입니다.")
            else:
                Pass = bcrypt.hashpw(Pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

                a = collection.insert_one({"name": ID, "password": Pass, "approved": False, "admin": False})
                print(a)
                if a:
                    QMessageBox.about(self, "Success", "가입 되었습니다")
                    self.gotologin()
                else:
                    QMessageBox.about(self, "Failed", "다시 진행해주세요")

            self.gotologin()
        else:
            QMessageBox.about(self, "Error", "Id와 PassWord를 입력해주세요.")


class Member_Page(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("ui/memberpage.ui", self)
        self.setFixedHeight(600)
        self.setFixedWidth(400)
        self.label.setText(user_name)
        self.label.setAlignment(Qt.AlignCenter)
        self.pushButton.clicked.connect(self.gotodetect)
        self.pushButton_2.clicked.connect(logoutstate)  # 로그아웃 버튼
        self.pushButton_4.clicked.connect(self.gotodb)  # 데이터 베이스 접근 버튼 -> 업로드 다운로드
        self.pushButton_3.clicked.connect(QCoreApplication.instance().quit)  # quit 버튼 (종료)

    def gotodb(self):
        db = DB_Download('member')
        widget.addWidget(db)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotodetect(self):
        detect = Detect('member')
        widget.addWidget(detect)
        widget.setCurrentIndex(widget.currentIndex() + 1)


class DB_Download(QMainWindow):  # 로그인후 db 접근 페이지
    def __init__(self, level):
        super().__init__()
        loadUi("ui/memberdb.ui", self)
        self.setFixedHeight(600)
        self.setFixedWidth(400)
        self.level = level
        self.db = client["test"]
        self.label.setText('Download')
        self.label.setAlignment(Qt.AlignCenter)
        self.pushButton_2.clicked.connect(logoutstate)  # 로그아웃 버튼
        self.pushButton.clicked.connect(self.download)  # 다운로드 버튼
        self.pushButton_5.clicked.connect(self.switch)  # 업로드 버튼
        self.pushButton_4.clicked.connect(self.delete)  # db 삭제 버튼
        self.backButton.clicked.connect(self.back)
        self.listset()
        self.pushButton_3.clicked.connect(QCoreApplication.instance().quit)  # quit 버튼 (종료)

    def listset(self):
        self.listWidget.clear()
        a = self.db.list_collection_names()
        for data in a:
            self.listWidget.addItem(data)

    def back(self):
        if self.level == 'admin':
            admin = Admin_Page()
            widget.addWidget(admin)
            widget.setCurrentIndex(widget.currentIndex() + 1)
        else:
            mem = Member_Page()
            widget.addWidget(mem)
            widget.setCurrentIndex(widget.currentIndex() + 1)

    def download(self):
        if self.listWidget.currentItem():
            db_user = self.listWidget.currentItem().text()
            print(db_user)

            knownEncodings = []
            knownNames = []

            if db_user in listdir(data_path):
                pass

            collection = self.db[db_user]
            result = collection.find({"name": db_user},{"_id": False})

            for r in result:
                knownEncodings.append((r["128d"]))
                knownNames.append(db_user)

            data = {"encodings": knownEncodings, "names": knownNames}
            createFolder(data_path)
            f = open(data_path + db_user, 'wb')
            print(data)
            f.write(pickle.dumps(data))
            f.close()
            print(db_user + 'download 완료')
            QMessageBox.about(self, "Success", db_user + " 다운로드 완료.")

        else:
            QMessageBox.about(self, "Error", "다운로드할 사용자를 선택하세요")

    def switch(self):
        dbup = DB_Upload(self.level)
        widget.addWidget(dbup)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def delete(self):
        if self.listWidget.currentItem():
            user = self.listWidget.currentItem().text()
            print(user)
            collection = self.db[user]
            collection.drop()
            print(user + '삭제완료')
            self.listset()
            QMessageBox.about(self, "Success", user + " 삭제완료")

        else:
            QMessageBox.about(self, "Error", "삭제할 사용자를 선택하세요")


class DB_Upload(QMainWindow):
    def __init__(self, level):
        super().__init__()
        loadUi("ui/dbupload.ui", self)
        self.setFixedHeight(600)
        self.setFixedWidth(400)
        self.level = level
        self.db = client["test"]
        self.label.setText('Upload')
        self.label.setAlignment(Qt.AlignCenter)
        self.pushButton_2.clicked.connect(logoutstate)  # 로그아웃 버튼
        self.pushButton.clicked.connect(self.upload)  # 다운로드 버튼
        self.pushButton_5.clicked.connect(self.switch)  # 업로드 버튼
        self.pushButton_4.clicked.connect(self.delete)  # db 삭제 버튼
        self.backButton.clicked.connect(self.back)
        self.listset()
        self.pushButton_3.clicked.connect(QCoreApplication.instance().quit)  # quit 버튼 (종료)

    def listset(self):
        self.listWidget.clear()
        load_data(data_path)
        for data in onlyfiles:
            self.listWidget.addItem(data)

    def back(self):
        if self.level == 'admin':
            admin = Admin_Page()
            widget.addWidget(admin)
            widget.setCurrentIndex(widget.currentIndex() + 1)
        else:
            mem = Member_Page()
            widget.addWidget(mem)
            widget.setCurrentIndex(widget.currentIndex() + 1)

    def upload(self):
        if self.listWidget.currentItem():
            user = self.listWidget.currentItem().text()
            print(user)
            data = pickle.loads(open('users/' + user, "rb").read())
            collection = self.db[user]
            for encoding in data["encodings"]:
                collection.insert_one({"128d": list(encoding), "name": user})

            print("upload완료")
            QMessageBox.about(self, "Success", user + " 업로드 완료")
        else:
            QMessageBox.about(self, "Error", "업로드할 사용자를 선택하세요")

    def switch(self):   # download 로 바꿔줌
        dbdown = DB_Download(self.level)
        widget.addWidget(dbdown)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def delete(self):
        if self.listWidget.currentItem():
            user = self.listWidget.currentItem().text()
            file = 'users/' + user

            if os.path.isfile(file):  # 선택한 파일이 존재할경우에
                response = QMessageBox.question(self, 'Message', 'Are you sure to delete?',
                                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                print(response)
                if response == QMessageBox.Yes:
                    os.remove(file)  # 파일을 삭제한다
                    self.listset()
                    QMessageBox.about(self, "INFO", "파일" + user + "의 삭제가 완료 되었습니다")  # 삭제완료 메세지 박스로 알려준다
                else:
                    QMessageBox.about(self, "CANCEL", "파일" + user + "의 삭제를 취소하였습니다")
            else:
                QMessageBox.about(self, "Error",
                                            "삭제할 파일이 존재하지 않습니다다")  # 파일이 존재하지 않을 경우에 메세지박스로 알려준다(정상적인 상황에서 발생할수 없는 오류)
        else:
            QMessageBox.about(self, "CANCEL", "삭제할 사용자를 선택해주세요")


class Admin_Page(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("ui/adminpage.ui", self)
        self.setFixedHeight(600)
        self.setFixedWidth(400)
        self.label.setText(user_name)
        self.label.setAlignment(Qt.AlignCenter)
        self.pushButton.clicked.connect(self.gotodetect)
        self.pushButton_2.clicked.connect(logoutstate)  # 로그아웃 버튼
        self.pushButton_4.clicked.connect(self.gotodb)  # 데이터 베이스 접근 버튼 -> 업로드 다운로드
        self.pushButton_5.clicked.connect(self.gotoapp)
        self.pushButton_3.clicked.connect(QCoreApplication.instance().quit)  # quit 버튼 (종료)

    def gotodb(self):
        db = DB_Download('admin')
        widget.addWidget(db)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotodetect(self):
        detect = Detect('admin')
        widget.addWidget(detect)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotoapp(self):
        apr = Approve()
        apr.exec_()


class Approve(QDialog):
    def __init__(self):
        super().__init__()
        loadUi("ui/regcheck.ui", self)
        self.setFixedHeight(300)
        self.setFixedWidth(600)
        self.db = client["member"]
        self.collection = self.db["member"]
        self.label.setText('승인대기')
        self.label_2.setText('승인완료')
        self.listset()
        self.label.setAlignment(Qt.AlignCenter)
        self.label_2.setAlignment(Qt.AlignCenter)

        self.pushButton.clicked.connect(self.app_user)

        self.pushButton_2.clicked.connect(self.un_user)

    def listset(self):
        self.listWidget.clear()
        self.listWidget_2.clear()

        a = self.collection.find({"approved": False})
        b = self.collection.find({"approved": True, "admin": False})
        print(a)
        for unapp in a:

            self.listWidget.addItem(unapp['name'])

        for app in b:

            self.listWidget_2.addItem(app['name'])

    def app_user(self):  # 승인 안된 회원 리스트에서 선택하여 승인 시켜주는 함수

        if self.listWidget.currentItem():
            selected_user = self.listWidget.currentItem().text()
            print(selected_user)

            self.collection.update({"name": selected_user}, {"$set": {"approved": True}})
            self.listset()
        else:
            print("check")

    def un_user(self):
        if self.listWidget_2.currentItem():

            selected_user = self.listWidget_2.currentItem().text()
            print(selected_user)

            self.collection.update({"name": selected_user}, {"$set": {"approved": False}})
            self.listset()
        else:
            print("2222")


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    home = Home_Screen()
    widget = QtWidgets.QStackedWidget()
    widget.addWidget(home)
    widget.show()
    app.exec_()
