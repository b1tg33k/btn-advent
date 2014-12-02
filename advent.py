import time
import sys
from PySide import QtGui, QtWebKit, QtCore, QtNetwork

DATA_DIR = QtGui.QDesktopServices.storageLocation(QtGui.QDesktopServices.DataLocation)
REFRESH_INTERVAL = 1000 * 3600 * 3  # 3 hours

class MyTimer(QtCore.QTimer):
    def start(self, *args, **kwargs):
        self._startTime = time.time()
        super(MyTimer, self).start(*args, **kwargs)

    def remainingTime(self):
        return self._startTime + self.interval() / 1000 - time.time()


class Window(QtGui.QDialog):
    def __init__(self, parent=None):
        '''A mess'''
        super(Window, self).__init__(parent)
        self.loggedIn = True

        self.settings = QtCore.QSettings('btn-advent', 'a')
        self.setWindowTitle('BTN Advent Calender')

        self.systemTrayIcon = QtGui.QSystemTrayIcon(self)
        self.systemTrayIcon.activated.connect(self._showWindow)
        self.systemTrayIcon.show()
        self.rightClickMenu = QtGui.QMenu()
        self.rightClickMenu.addAction('Quit', self.reject)
        self.systemTrayIcon.setContextMenu(self.rightClickMenu)

        self.layout = QtGui.QVBoxLayout()

        self.statusLabel = QtGui.QLabel('Hello World!')
        self.view = QtWebKit.QWebView(self)
        self.cookieJar = QtNetwork.QNetworkCookieJar()
        self.view.page().networkAccessManager().setCookieJar(self.cookieJar)

        self._loadCookies()
        self._loadSysTrayIcon()

        self.layout.addWidget(self.statusLabel, stretch=5)
        self.layout.addWidget(self.view, stretch=95)

        self.setLayout(self.layout)
        self.view.loadFinished.connect(self.checkPrize)

        # This updates the status label
        self.statusTimer = QtCore.QTimer(self)
        self.statusTimer.timeout.connect(self.updateStatus)
        self.statusTimer.start(1000)

        # This timer refreshes the page periodically
        self.loadTimer = MyTimer(self)
        self.loadTimer.timeout.connect(self.loader)
        self.loadTimer.setSingleShot(True)
        self.loadTimer.start(REFRESH_INTERVAL)

        self.showMaximized()

        self.loader()

    def _loadCookies(self):
        cookies = self.settings.value('cookieStore') or None
        if cookies:
            parsedCookies = []
            for raw_cookie in cookies:
                cookie_list = QtNetwork.QNetworkCookie.parseCookies(raw_cookie)
                for cookie in cookie_list:
                    parsedCookies.append(cookie)
            self.cookieJar.setAllCookies(parsedCookies)

    def _loadSysTrayIcon(self):
        url = "https://broadcasthe.net/favicon.ico"
        self.nam = QtNetwork.QNetworkAccessManager()
        self.nam.finished.connect(self._setSysTrayIcon)
        self.nam.get(QtNetwork.QNetworkRequest(QtCore.QUrl(url)))

    def _setSysTrayIcon(self, response):
        img = QtGui.QImage()
        img.loadFromData(response.readAll())
        icon = QtGui.QPixmap.fromImage(img)
        self.systemTrayIcon.setIcon(icon)

    def loader(self):
        self.view.load(QtCore.QUrl('https://broadcasthe.net/advent.php?action=claimprize'))
        self.view.show()

    def checkPrize(self):
        if 'claimprize' not in str(self.view.url()):
            return
        self.loadTimer.setInterval(REFRESH_INTERVAL)
        self.loadTimer.start()

    def updateStatus(self):
        if 'login.php' in str(self.view.url()) and self.loggedIn == True:
            self.systemTrayIcon.showMessage('Action required', 'You need to log-in')
            self.loggedIn = False

        if 'login.php' not in str(self.view.url()) and self.loggedIn == False:
            self.loggedIn = True

        cookieJar = self.view.page().networkAccessManager().cookieJar().allCookies()
        cookies = [cookie.toRawForm() for cookie in cookieJar]

        self.settings.setValue('cookieStore', cookies)

        remaining = int(self.loadTimer.remainingTime())
        self.statusLabel.setText('Reloading in {0}s'.format(remaining))

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.systemTrayIcon.showMessage('Running', 'Running in background, right click to quit')

    def _showWindow(self, reason):
        if reason == QtGui.QSystemTrayIcon.DoubleClick:
            if self.isHidden():
                self.show()
            else:
                self.hide()

def exec_():
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    exec_()