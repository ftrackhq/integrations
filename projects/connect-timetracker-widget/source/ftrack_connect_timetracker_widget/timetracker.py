# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import operator
import time
import logging

from ftrack_connect.qt import QtWidgets, QtCore, QtGui

import ftrack_connect.ui.application
import ftrack_connect.ui.widget.overlay
import ftrack_connect.usage
import ftrack_connect.ui.widget.item_list
import ftrack_connect.ui.widget.label
import ftrack_connect.ui.widget.line_edit

logger = logging.getLogger('ftrack_connect.plugin.timetracker')

import re
import math
import qtawesome as qta
import ftrack_connect.error


class DurationParser(object):
    '''Parse human readable time durations into seconds.'''

    def __init__(self):
        '''Initialise parser.'''
        self._unit = dict(day=60 * 60 * 24, hour=60 * 60, minute=60, second=1)

        # Build expressions.
        self._expressions = []

        # Hour, minute, seconds specified using unit classifiers.
        # Example: 3.5hours 2 mins, 1s
        value = r'\d+(?:\.\d+)?'
        day = r'(?P<day>{0})\s*(?:days?|dys?|d)'.format(value)
        hour = r'(?P<hour>{0})\s*(?:hours?|hrs?|h)'.format(value)
        minute = r'(?P<minute>{0})\s*(?:minutes?|mins?|m)'.format(value)
        second = r'(?P<second>{0})\s*(?:seconds?|secs?|s)'.format(value)
        separators = r'[\s,/-]*'

        expression = ''
        for entry in [day, hour, minute, second]:
            expression += r'(?:{0})?{1}'.format(entry, separators)

        expression += '$'
        self._expressions.append(re.compile(expression, re.IGNORECASE))

        # Minute, second clock format.
        # Example: 1:30 min -> 1 minute and 30 seconds
        self._expressions.append(
            re.compile(
                r'(?P<minute>\d+):(?P<second>\d+)\s*(?:minutes?|mins?|m)\s*$',
                re.IGNORECASE,
            )
        )

        # Hour, minute clock format.
        # Example: 1:30 -> 1 hour and 30 minutes
        self._expressions.append(
            re.compile(
                r'(?P<hour>\d+):(?P<minute>\d+)\s*(?:hours?|hrs?|h)?\s*$',
                re.IGNORECASE,
            )
        )

        # Hour, minute, second clock formats.
        # Example: 1:30:45 -> 1 hour, 30 minutes and 45 seconds.
        self._expressions.append(
            re.compile(
                r'(?P<hour>\d+):(?P<minute>\d+):(?P<second>\d+)$',
                re.IGNORECASE,
            )
        )

    def parse(self, text):
        '''Return *text* parsed into seconds as float.

        Supported formats are:

            * unit-less integer - Interpreted as minutes. Example: "90" is 1
              hour and 30 minutes.

            * unit-less float - Interpreted as hours. Example: "1.5" is 1 hour
              and 30 minutes.

            * hh:mm - Specify hours and minutes. Can use padded or unpadded
              digits. Example: "03:42" is 3 hours and 42 minutes.

            * mm:ss min - Specify minutes and seconds. Can use padded or
              unpadded digits. Example: "03:42 min" is 3 minutes and 42 seconds.

            * hh:mm:ss - Specify hours, minutes and seconds. Can use padded or
              unpadded digits. Example: "8:45:03" is 8 hours, 43 minutes and 3
              seconds.

            * {hours unit} {minutes unit} {seconds unit} - Can enter specific
              values for each optional unit. Valid unit specifiers include both
              full words and abbreviations. Example: "1h 2 minutes 5 sec"
              It is also possible to use fractions. Example: "1.5h 15seconds"

        Raise :exc:`~ftrack_connect.error.ParseError` if *text* could not be
        parsed.

        '''
        text = text.strip()

        # Interpret empty string as 0
        if not text:
            return 0.0

        # Interpret unit-less integer value as minutes.
        try:
            seconds = int(text)
        except ValueError:
            pass
        else:
            return float(self._unit['minute'] * seconds)

        # Interpret unit-less float value as hours.
        try:
            seconds = float(text)
        except ValueError:
            pass
        else:
            return self._unit['hour'] * seconds

        # Process as expression.
        for expression in self._expressions:
            match = expression.match(text)
            if match:
                seconds = 0.0
                for key, value in match.groupdict().items():
                    if value is not None:
                        seconds += self._unit[key] * float(value)

                return seconds

        raise ftrack_connect.error.ParseError(
            'Failed to parse duration {0}'.format(text.encode('utf-8'))
        )


class DurationFormatter(object):
    '''Format durations in seconds into human readable strings.'''

    def format(self, seconds):
        '''Return human readable string representing *seconds* duration.'''
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        hours = int(hours)
        minutes = int(minutes)
        seconds = int(math.ceil(seconds))

        if seconds == 60:
            minutes += 1
            seconds = 0

        if minutes == 60:
            hours += 1
            minutes = 0

        if not hours and not minutes:
            text = '{0} sec'.format(seconds)
        elif not hours:
            text = '{0:02d}:{1:02d} min'.format(minutes, seconds)
        else:
            text = '{0:02d}:{1:02d}:{2:02d}'.format(hours, minutes, seconds)

        return text


class Timer(QtWidgets.QFrame):
    '''Timer for logging time.'''

    #: Signal when time value edited manually.
    timeEdited = QtCore.Signal(object)

    #: Signal when time value changed either manually or programatically.
    timeChanged = QtCore.Signal(object)

    #: Signal when timer started passing elapsed time.
    started = QtCore.Signal(object)

    #: Signal when timer stopped passing elapsed time.
    stopped = QtCore.Signal(object)

    #: Signal when timer paused passing elapsed time.
    paused = QtCore.Signal(object)

    #: Signal when timer resumed passing elapsed time.
    resumed = QtCore.Signal(object)

    #: Timer stopped state.
    STOPPED = 'STOPPED'

    #: Timer paused state.
    PAUSED = 'PAUSED'

    #: Time running state.
    RUNNING = 'RUNNING'

    def __init__(self, title=None, description=None, time=0, parent=None):
        '''Initialise timer.

        *title* should be the title entry to display for the time log whilst
        *description* can provide an optional longer description.

        *time* should be the initial value to set elapsed time to.

        *parent* should be the optional parent of this widget.

        '''
        super(Timer, self).__init__(parent=parent)
        self.setObjectName('timer')

        self._state = self.STOPPED
        self._timer = None
        self._tick = None
        self._tickInterval = 1000
        self._elapsed = 0

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        self.labelLayout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.labelLayout, stretch=1)

        self.titleLabel = ftrack_connect.ui.widget.label.Label()
        self.titleLabel.setProperty('title', True)
        self.labelLayout.addWidget(self.titleLabel)

        self.descriptionLabel = ftrack_connect.ui.widget.label.Label()
        self.labelLayout.addWidget(self.descriptionLabel)

        self.timeField = ftrack_connect.ui.widget.line_edit.LineEdit()
        self.timeField.setObjectName('timeField')
        self.timeField.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.timeField)

        self.toggleButton = QtWidgets.QPushButton('Start')
        self.toggleButton.setObjectName('primary')
        self.toggleButton.setProperty('mode', 'start')

        layout.addWidget(self.toggleButton)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )

        # Install event filter at application level in order to manage focus
        # behaviour correctly.
        application = QtCore.QCoreApplication.instance()
        application.installEventFilter(self)

        # Connect events.
        self.toggleButton.clicked.connect(self.toggle)

        # Set initial values.
        self.setValue(
            {'title': title, 'description': description, 'time': time}
        )

    def eventFilter(self, obj, event):
        '''Filter *event* sent to *obj*.'''
        if obj == self.timeField:
            if event.type() == QtCore.QEvent.FocusIn:
                self._onTimeFieldFocused()

            elif event.type() == QtCore.QEvent.FocusOut:
                self._onTimeFieldBlurred()

            elif event.type() == QtCore.QEvent.KeyPress:
                if event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
                    self.timeField.clearFocus()
                    return True

                elif event.key() == QtCore.Qt.Key_Escape:
                    # Cancel any currently entered value.
                    self.setTime(self.time())
                    self.timeField.clearFocus()
                    return True

        else:
            if event.type() == QtCore.QEvent.MouseButtonRelease:
                self.timeField.clearFocus()

        # Let event propagate.
        return False

    def _onTimeFieldFocused(self):
        '''Handle time field receiving focus.'''
        if self.state() is self.RUNNING:
            self.pause()

        # Force disabling of toggle button.
        self.toggleButton.setDisabled(True)

        # Select all text in line edit. Note: Has to be done using a timer as
        # otherwise the immediately following click event would deselect the
        # text.
        QtCore.QTimer.singleShot(0, self.timeField.selectAll)

    def _onTimeFieldBlurred(self):
        '''Handle time field losing focus.'''
        try:
            time = DurationParser().parse(self.timeField.text())
        except ftrack_connect.error.ParseError:
            # Revert to previous correct value.
            # TODO: Indicate to user that entered value is invalid.
            self.setTime(self.time())
        else:
            if time != self.time():
                self.timeEdited.emit(time)

            self.setTime(time)

        if self.state() is self.PAUSED:
            self.resume()

        # Force enabling of toggle button.
        self.toggleButton.setEnabled(True)

    def _updateInterface(self):
        '''Update interface to reflect current state and force style refresh.'''
        state = self.state()

        if state is self.RUNNING:
            self.toggleButton.setText('Stop')
            self.toggleButton.setProperty('mode', 'stop')

        elif state is self.STOPPED:
            self.toggleButton.setText('Start')
            self.toggleButton.setProperty('mode', 'start')

        # Force re-evaluation of dynamic stylesheet values based on new
        # properties.
        self.toggleButton.style().unpolish(self.toggleButton)
        self.toggleButton.style().polish(self.toggleButton)
        self.toggleButton.update()

    def _startTimer(self):
        '''Start internal timer.'''
        self._tick = time.time()
        self._timer = self.startTimer(self._tickInterval)

    def _stopTimer(self):
        '''Stop internal timer.'''
        if self._timer is not None:
            self.killTimer(self._timer)

        self._timer = None
        self._tick = None

    def timerEvent(self, event):
        '''Handle timer *event*.'''
        if self._tick is not None:
            now = time.time()
            self.setTime(self._elapsed + (now - self._tick))
            self._tick = now

    def start(self):
        '''Start the timer.

        Raise :exc:`ftrack_connect.error.InvalidState` if timer is not currently
        stopped.

        '''
        self.clear()
        state = self.state()
        if state is not self.STOPPED:
            raise ftrack_connect.error.InvalidStateError(
                'Cannot start timer in {0} state.'.format(state)
            )

        self._startTimer()
        self._state = self.RUNNING
        self.started.emit(self.time())

        self._updateInterface()

    def stop(self):
        '''Stop the timer.

        Raise :exc:`ftrack_connect.error.InvalidState` if timer is already
        stopped.

        '''
        state = self.state()
        if state is self.STOPPED:
            raise ftrack_connect.error.InvalidStateError(
                'Cannot stop timer in {0} state.'.format(state)
            )

        if state is not self.PAUSED:
            # Ensure correct time recorded. Note: Not done when transitioning
            # from PAUSED to STOPPED as time entered in PAUSED state should be
            # taken as is.
            self.timerEvent(QtCore.QTimerEvent(0))

        self._stopTimer()
        self._state = self.STOPPED
        self.stopped.emit(self.time())

        self._updateInterface()

    def pause(self):
        '''Pause the timer without updating state.

        Raise :exc:`ftrack_connect.error.InvalidState` if timer is not running.

        '''
        state = self.state()
        if state is not self.RUNNING:
            raise ftrack_connect.error.InvalidStateError(
                'Cannot pause timer in {0} state.'.format(state)
            )

        self._stopTimer()
        self._state = self.PAUSED
        self.paused.emit(self.time())

        self._updateInterface()

    def resume(self):
        '''Resume a paused timer without updating state.

        Raise :exc:`ftrack_connect.error.InvalidState` if timer is not paused.

        '''
        state = self.state()
        if state is not self.PAUSED:
            raise ftrack_connect.error.InvalidStateError(
                'Cannot resume timer in {0} state.'.format(state)
            )

        self._startTimer()
        self._state = self.RUNNING
        self.resumed.emit(self.time())

        self._updateInterface()

    def state(self):
        '''Return current state of timer.

        Possible states are:

            * :attr:`STOPPED`
            * :attr:`PAUSED`
            * :attr:`RUNNING`

        .. note::

            State can only be changed using the provided control methods (
            :meth:`start`, :meth:`stop`, :meth:`pause`, :meth:`resume`.

        '''
        return self._state

    def toggle(self):
        '''Toggle the timer state between stopped and started.

        .. note::

            If timer is paused will transition to stopped state.

        '''
        state = self.state()
        if state is self.STOPPED:
            self.start()
        else:
            self.stop()

    def reset(self):
        '''Reset timer and elapsed time.'''
        self.stop()
        self._elapsed = 0

    def clear(self):
        '''Clear all values.'''

        self.setValue(
            {
                'title': self.title(),
                'description': self.description(),
                'time': 0,
            }
        )

    def value(self):
        '''Return dictionary with component data.'''
        return {
            'title': self.title(),
            'description': self.description(),
            'time': self.time(),
        }

    def setValue(self, value):
        '''Set all attributes from *value*.'''
        self.setTitle(value.get('title', None))
        self.setDescription(value.get('description', None))
        self.setTime(value.get('time', 0))

    def title(self):
        '''Return title.'''
        return self.titleLabel.text()

    def setTitle(self, title):
        '''Set *title*.'''
        self.titleLabel.setText(title)

    def description(self):
        '''Return description.'''
        return self.descriptionLabel.text()

    def setDescription(self, description):
        '''Set *description*.'''
        self.descriptionLabel.setText(description)

    def time(self):
        '''Return time elapsed in seconds.'''
        return self._elapsed

    def setTime(self, time):
        '''Set *time* elapsed in seconds.'''
        if time is None:
            time = 0

        changed = time == self.time()
        self._elapsed = time
        text = DurationFormatter().format(time)
        self.timeField.setText(text)

        if changed:
            self.timeChanged.emit(time)


class TimeLog(QtWidgets.QWidget):
    '''Represent a time log.'''

    selected = QtCore.Signal(object)

    def __init__(self, title=None, description=None, data=None, parent=None):
        '''Initialise time log.

        *title* should be the title entry to display for the time log whilst
        *description* can provide an optional longer description.

        *data* is optional data that can be stored for future reference (for
        example a link to an ftrack task that the time log represents).

        *parent* should be the optional parent of this widget.

        '''
        super(TimeLog, self).__init__(parent=parent)
        self.setObjectName('time-log')
        self._data = None

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        self.labelLayout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.labelLayout, stretch=1)

        self.titleLabel = ftrack_connect.ui.widget.label.Label()
        self.titleLabel.setProperty('title', True)
        self.labelLayout.addWidget(self.titleLabel)

        self.descriptionLabel = ftrack_connect.ui.widget.label.Label()
        self.labelLayout.addWidget(self.descriptionLabel)

        # TODO: Add theme support.
        playIcon = qta.icon('mdi6.play', color='#FFDD86', scale_factor=1.5)

        self.playButton = QtWidgets.QPushButton(playIcon, '')
        self.playButton.setFlat(True)
        self.playButton.clicked.connect(self._onPlayButtonClicked)
        layout.addWidget(self.playButton)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )

        # Set initial values.
        self.setValue(
            {'title': title, 'description': description, 'data': data}
        )

    def title(self):
        '''Return title.'''
        return self.titleLabel.text()

    def setTitle(self, title):
        '''Set *title*.'''
        self.titleLabel.setText(title)

    def description(self):
        '''Return description.'''
        return self.descriptionLabel.text()

    def setDescription(self, description):
        '''Set *description*.'''
        self.descriptionLabel.setText(description)

    def data(self):
        '''Return associated data.'''
        return self._data

    def setData(self, data):
        '''Set associated *data*.'''
        self._data = data

    def value(self):
        '''Return dictionary of current settings.'''
        return {
            'title': self.title(),
            'description': self.description(),
            'data': self.data(),
        }

    def setValue(self, value):
        '''Set all attributes from *value*.'''
        self.setTitle(value.get('title', None))
        self.setDescription(value.get('description', None))
        self.setData(value.get('data', None))

    def _onPlayButtonClicked(self):
        '''Handle playButton clicks.'''
        self.selected.emit(self)


class TimeLogList(ftrack_connect.ui.widget.item_list.ItemList):
    '''List time logs widget.'''

    itemSelected = QtCore.Signal(object)

    def __init__(self, parent=None, title=None, headerWidgets=None):
        '''Instantiate widget with optional *parent* and *title*.

        *headerWidgets* is an optional list of widgets to append to the header
        of the time log widget.

        '''
        super(TimeLogList, self).__init__(
            widgetFactory=self._createWidget,
            widgetItem=lambda widget: widget.value(),
            parent=parent,
        )
        self.setObjectName('time-log-list')
        self.list.setShowGrid(False)

        # Disable selection on internal list.
        self.list.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

        headerLayout = QtWidgets.QHBoxLayout()
        self.titleLabel = QtWidgets.QLabel(title)
        self.titleLabel.setProperty('title', True)

        headerLayout.addWidget(self.titleLabel, stretch=1)

        # TODO: Refacor and make use of QToolBar and QAction.
        # Also consider adding 'addAction'/'removeAction'.
        if headerWidgets:
            for widget in headerWidgets:
                headerLayout.addWidget(widget, stretch=0)

        self.layout().insertLayout(0, headerLayout)

    def setTitle(self, title):
        '''Set *title*.'''
        self.titleLabel.setText(title)

    def title(self):
        '''Return current title.'''
        self.titleLabel.text()

    def addItem(self, item, row=None):
        '''Add *item* at *row*.

        If *row* not specified then add to end of list.

        Return row item added at.

        '''
        row = super(TimeLogList, self).addItem(item, row=row)
        widget = self.list.widgetAt(row)

        # Connect the widget's selected signal to the itemSelected signal
        widget.selected.connect(self.itemSelected.emit)

        return row

    def _createWidget(self, item):
        '''Return time log widget for *item*.

        *item* should be a mapping of keyword arguments to pass to
        :py:class:`ftrack_connect.ui.widget.time_log.TimeLog`.

        '''
        if item is None:
            item = {}

        return TimeLog(**item)


class TimerOverlay(ftrack_connect.ui.widget.overlay.Overlay):
    '''Overlay for timer widget.'''

    def __init__(self, parent):
        '''Initialise.'''
        super(TimerOverlay, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        message = QtWidgets.QLabel('Select a task to activate timer.')
        message.setWordWrap(True)
        message.setAlignment(QtCore.Qt.AlignVCenter)
        layout.addWidget(message)

        # TODO: See if there is a way to stop Sass converting the rgba string
        # to the wrong value.
        self.setStyleSheet(
            '''
            #ftrack-connect-window TimerOverlay {
                background-color: rgba(128, 128, 128, 200);
            }
        '''
        )


class TimeTrackerBlockingOverlay(
    ftrack_connect.ui.widget.overlay.BlockingOverlay
):
    '''Custom blocking overlay for time tracker.'''

    def __init__(self, parent, message=''):
        '''Initialise.'''
        super(TimeTrackerBlockingOverlay, self).__init__(
            parent,
            message=message,
            icon=':ftrack/image/default/ftrackLogoGrey',
        )
        self.content.setMinimumWidth(350)
