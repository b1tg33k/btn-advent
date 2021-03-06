import time
import re
import sys
import random
from PySide import QtGui, QtWebKit, QtCore, QtNetwork

DATA_DIR = QtGui.QDesktopServices.storageLocation(QtGui.QDesktopServices.DataLocation)
REFRESH_INTERVAL = 1000 * 3600 # 1 hour

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

        self.settings = QtCore.QSettings('btn-advent', 'a')
        self.setWindowTitle('BTN Advent Calender')

        self.systemTrayIcon = QtGui.QSystemTrayIcon(self)
        self.systemTrayIcon.activated.connect(self._showWindow)
        defaultIcon = QtGui.QStyle.SP_ArrowUp
        self.systemTrayIcon.setIcon(self.style().standardIcon(defaultIcon))
        self.rightClickMenu = QtGui.QMenu()
        self.rightClickMenu.addAction('&Show window', self.show)
        self.rightClickMenu.addAction('&Quit', self.reject)
        self.systemTrayIcon.show()
        self.systemTrayIcon.setContextMenu(self.rightClickMenu)

        self.layout = QtGui.QVBoxLayout()

        self.statusLabel = QtGui.QLabel('Hello World!')
        self.view = QtWebKit.QWebView(self)
        self.view.hide()
        self.cookieJar = QtNetwork.QNetworkCookieJar()
        self.view.page().networkAccessManager().setCookieJar(self.cookieJar)

        self._loadCookies()
        self._loadSysTrayIcon()

        self.layout.addWidget(self.statusLabel, stretch=5)
        self.layout.addWidget(self.view, stretch=95)

        self.setLayout(self.layout)
        self.prizeStatus = ''
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
        url = "https://cdn.broadcasthe.net/common/present.png"
        self.nam = QtNetwork.QNetworkAccessManager()
        self.nam.finished.connect(self._setSysTrayIcon)
        self.nam.get(QtNetwork.QNetworkRequest(QtCore.QUrl(url)))

    def _setSysTrayIcon(self, response):
        img = QtGui.QImage()
        img.loadFromData(response.readAll())
        icon = QtGui.QPixmap.fromImage(img)
        self.systemTrayIcon.setIcon(icon)
        self.systemTrayIcon.show()

    def loader(self):
        self.view.load(QtCore.QUrl('https://broadcasthe.net/advent.php?action=claimprize'))

    def checkPrize(self):
        # Backup current cookies
        cookieJar = self.view.page().networkAccessManager().cookieJar().allCookies()
        cookies = [cookie.toRawForm() for cookie in cookieJar]
        self.settings.setValue('cookieStore', cookies)

        if 'login.php' in str(self.view.url()):
            self.view.show()
            self.adjustSize()
            self.systemTrayIcon.showMessage('Action required', 'You need to log-in')
        else:
            self.view.hide()
            self.adjustSize()

        if 'claimprize' not in str(self.view.url()):
            return
        html = self.view.page().mainFrame().toHtml()
        prizes = re.search('The prizes you have won so far are: (.*?)<', html)
        if prizes:
            prizes = '\n'.join(prizes.group(1).split(', '))
            self.prizeStatus = 'Currently won prizes:\n{0}'.format(prizes)

        nextPrize = re.search('Please try again in.*([0-9]+)d ([0-9]+)h ([0-9]+)m ([0-9]+)s', html)
        nextReload = REFRESH_INTERVAL
        if nextPrize:
            try:
                days, hours, minutes, seconds = map(int, nextPrize.groups())
                nextReload = 1000 * (days * 86400 +
                                     hours * 3600 +
                                     minutes * 60 +
                                     seconds +
                                     random.randint(10, 100))
            except AttributeError:
                pass
        self.loadTimer.setInterval(nextReload)
        self.loadTimer.start()

    def getStatusString(self):
        remaining = int(self.loadTimer.remainingTime())
        hours = remaining / 3600
        minutes = (remaining - hours * 3600) / 60

        return '''Reloading in {0}s ({1}h {2}m)\n
{3}'''.format(remaining, int(hours), int(minutes), self.prizeStatus)

    def updateStatus(self):
        status = self.getStatusString()
        self.statusLabel.setText(status)
        self.systemTrayIcon.setToolTip(status)

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
