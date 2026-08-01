# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.8.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QComboBox, QDoubleSpinBox,
    QFormLayout, QFrame, QGroupBox, QHBoxLayout,
    QLabel, QMainWindow, QPushButton, QSizePolicy,
    QSpacerItem, QSpinBox, QStatusBar, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1102, 882)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout_5 = QHBoxLayout(self.centralwidget)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMinimumSize(QSize(200, 200))
        self.label_3.setMaximumSize(QSize(200, 200))

        self.horizontalLayout.addWidget(self.label_3)

        self.spnTargetPieces = QSpinBox(self.centralwidget)
        self.spnTargetPieces.setObjectName(u"spnTargetPieces")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spnTargetPieces.sizePolicy().hasHeightForWidth())
        self.spnTargetPieces.setSizePolicy(sizePolicy)
        self.spnTargetPieces.setMinimumSize(QSize(300, 200))
        self.spnTargetPieces.setMaximumSize(QSize(300, 200))
        font = QFont()
        font.setPointSize(72)
        self.spnTargetPieces.setFont(font)
        self.spnTargetPieces.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.spnTargetPieces.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spnTargetPieces.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spnTargetPieces.setMinimum(1)
        self.spnTargetPieces.setMaximum(999)
        self.spnTargetPieces.setValue(100)

        self.horizontalLayout.addWidget(self.spnTargetPieces)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.line_2 = QFrame(self.centralwidget)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_2.addWidget(self.line_2)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_4 = QLabel(self.centralwidget)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setMinimumSize(QSize(200, 200))
        self.label_4.setMaximumSize(QSize(200, 200))

        self.horizontalLayout_2.addWidget(self.label_4)

        self.lblTotalPieces = QLabel(self.centralwidget)
        self.lblTotalPieces.setObjectName(u"lblTotalPieces")
        self.lblTotalPieces.setMinimumSize(QSize(300, 200))
        self.lblTotalPieces.setMaximumSize(QSize(300, 200))
        self.lblTotalPieces.setFont(font)
        self.lblTotalPieces.setScaledContents(False)
        self.lblTotalPieces.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_2.addWidget(self.lblTotalPieces)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.line_3 = QFrame(self.centralwidget)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.Shape.HLine)
        self.line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_2.addWidget(self.line_3)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_8 = QLabel(self.centralwidget)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setMinimumSize(QSize(200, 200))
        self.label_8.setMaximumSize(QSize(200, 200))

        self.horizontalLayout_3.addWidget(self.label_8)

        self.lblActWeight = QLabel(self.centralwidget)
        self.lblActWeight.setObjectName(u"lblActWeight")
        self.lblActWeight.setMinimumSize(QSize(300, 200))
        self.lblActWeight.setMaximumSize(QSize(300, 200))
        font1 = QFont()
        font1.setPointSize(36)
        self.lblActWeight.setFont(font1)
        self.lblActWeight.setScaledContents(False)
        self.lblActWeight.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_3.addWidget(self.lblActWeight)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_2)


        self.horizontalLayout_5.addLayout(self.verticalLayout_2)

        self.line = QFrame(self.centralwidget)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.VLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout_5.addWidget(self.line)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.btnStart = QPushButton(self.centralwidget)
        self.btnStart.setObjectName(u"btnStart")
        self.btnStart.setMinimumSize(QSize(180, 0))
        self.btnStart.setMaximumSize(QSize(16777215, 16777215))
        font2 = QFont()
        font2.setPointSize(20)
        self.btnStart.setFont(font2)

        self.verticalLayout.addWidget(self.btnStart)

        self.btnStop = QPushButton(self.centralwidget)
        self.btnStop.setObjectName(u"btnStop")
        self.btnStop.setFont(font2)

        self.verticalLayout.addWidget(self.btnStop)

        self.btnClear = QPushButton(self.centralwidget)
        self.btnClear.setObjectName(u"btnClear")
        self.btnClear.setEnabled(False)
        self.btnClear.setFont(font2)

        self.verticalLayout.addWidget(self.btnClear)

        self.groupBox_5 = QGroupBox(self.centralwidget)
        self.groupBox_5.setObjectName(u"groupBox_5")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.groupBox_5.sizePolicy().hasHeightForWidth())
        self.groupBox_5.setSizePolicy(sizePolicy1)
        self.groupBox_5.setMaximumSize(QSize(16777215, 16777215))
        self.formLayout_2 = QFormLayout(self.groupBox_5)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label_20 = QLabel(self.groupBox_5)
        self.label_20.setObjectName(u"label_20")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label_20.sizePolicy().hasHeightForWidth())
        self.label_20.setSizePolicy(sizePolicy2)
        self.label_20.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_20)

        self.spnForcePieces = QSpinBox(self.groupBox_5)
        self.spnForcePieces.setObjectName(u"spnForcePieces")
        sizePolicy.setHeightForWidth(self.spnForcePieces.sizePolicy().hasHeightForWidth())
        self.spnForcePieces.setSizePolicy(sizePolicy)
        self.spnForcePieces.setMinimumSize(QSize(0, 0))
        self.spnForcePieces.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.spnForcePieces.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.spnForcePieces.setMinimum(0)
        self.spnForcePieces.setMaximum(999)
        self.spnForcePieces.setValue(0)

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.spnForcePieces)


        self.verticalLayout.addWidget(self.groupBox_5)

        self.btnForce = QPushButton(self.centralwidget)
        self.btnForce.setObjectName(u"btnForce")
        self.btnForce.setEnabled(True)
        self.btnForce.setFont(font2)

        self.verticalLayout.addWidget(self.btnForce)

        self.verticalSpacer = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName(u"groupBox")
        self.formLayout = QFormLayout(self.groupBox)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.label_21 = QLabel(self.groupBox)
        self.label_21.setObjectName(u"label_21")
        sizePolicy2.setHeightForWidth(self.label_21.sizePolicy().hasHeightForWidth())
        self.label_21.setSizePolicy(sizePolicy2)
        self.label_21.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_21)

        self.lblState = QLabel(self.groupBox)
        self.lblState.setObjectName(u"lblState")
        self.lblState.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.lblState)

        self.label_10 = QLabel(self.groupBox)
        self.label_10.setObjectName(u"label_10")
        sizePolicy2.setHeightForWidth(self.label_10.sizePolicy().hasHeightForWidth())
        self.label_10.setSizePolicy(sizePolicy2)
        self.label_10.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_10)

        self.lblDeltaWeight = QLabel(self.groupBox)
        self.lblDeltaWeight.setObjectName(u"lblDeltaWeight")
        self.lblDeltaWeight.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.lblDeltaWeight)

        self.label_6 = QLabel(self.groupBox)
        self.label_6.setObjectName(u"label_6")
        sizePolicy2.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy2)
        self.label_6.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_6)

        self.lblAvgWeight = QLabel(self.groupBox)
        self.lblAvgWeight.setObjectName(u"lblAvgWeight")
        self.lblAvgWeight.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.lblAvgWeight)

        self.label_9 = QLabel(self.groupBox)
        self.label_9.setObjectName(u"label_9")
        sizePolicy2.setHeightForWidth(self.label_9.sizePolicy().hasHeightForWidth())
        self.label_9.setSizePolicy(sizePolicy2)
        self.label_9.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_9)

        self.lblTolHigh = QLabel(self.groupBox)
        self.lblTolHigh.setObjectName(u"lblTolHigh")
        self.lblTolHigh.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.lblTolHigh)

        self.label_11 = QLabel(self.groupBox)
        self.label_11.setObjectName(u"label_11")
        sizePolicy2.setHeightForWidth(self.label_11.sizePolicy().hasHeightForWidth())
        self.label_11.setSizePolicy(sizePolicy2)
        self.label_11.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_11)

        self.lblTolLow = QLabel(self.groupBox)
        self.lblTolLow.setObjectName(u"lblTolLow")
        self.lblTolLow.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.lblTolLow)

        self.label_12 = QLabel(self.groupBox)
        self.label_12.setObjectName(u"label_12")
        sizePolicy2.setHeightForWidth(self.label_12.sizePolicy().hasHeightForWidth())
        self.label_12.setSizePolicy(sizePolicy2)
        self.label_12.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.label_12)

        self.lblLastBaseWeight = QLabel(self.groupBox)
        self.lblLastBaseWeight.setObjectName(u"lblLastBaseWeight")
        self.lblLastBaseWeight.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.lblLastBaseWeight)

        self.label_15 = QLabel(self.groupBox)
        self.label_15.setObjectName(u"label_15")
        sizePolicy2.setHeightForWidth(self.label_15.sizePolicy().hasHeightForWidth())
        self.label_15.setSizePolicy(sizePolicy2)
        self.label_15.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.label_15)

        self.lblLastStableWeight = QLabel(self.groupBox)
        self.lblLastStableWeight.setObjectName(u"lblLastStableWeight")
        self.lblLastStableWeight.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(6, QFormLayout.FieldRole, self.lblLastStableWeight)


        self.verticalLayout.addWidget(self.groupBox)

        self.groupBox_2 = QGroupBox(self.centralwidget)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.formLayout_3 = QFormLayout(self.groupBox_2)
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.label_14 = QLabel(self.groupBox_2)
        self.label_14.setObjectName(u"label_14")
        sizePolicy2.setHeightForWidth(self.label_14.sizePolicy().hasHeightForWidth())
        self.label_14.setSizePolicy(sizePolicy2)
        self.label_14.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label_14)

        self.dspnTolerancePercent = QDoubleSpinBox(self.groupBox_2)
        self.dspnTolerancePercent.setObjectName(u"dspnTolerancePercent")
        self.dspnTolerancePercent.setMinimumSize(QSize(0, 0))
        self.dspnTolerancePercent.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.dspnTolerancePercent.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.dspnTolerancePercent.setDecimals(2)
        self.dspnTolerancePercent.setMinimum(1.000000000000000)
        self.dspnTolerancePercent.setMaximum(20.000000000000000)
        self.dspnTolerancePercent.setSingleStep(1.000000000000000)

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.dspnTolerancePercent)

        self.label_18 = QLabel(self.groupBox_2)
        self.label_18.setObjectName(u"label_18")
        sizePolicy2.setHeightForWidth(self.label_18.sizePolicy().hasHeightForWidth())
        self.label_18.setSizePolicy(sizePolicy2)
        self.label_18.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.label_18)

        self.spnMaxBatchPieces = QSpinBox(self.groupBox_2)
        self.spnMaxBatchPieces.setObjectName(u"spnMaxBatchPieces")
        self.spnMaxBatchPieces.setMinimumSize(QSize(0, 0))
        self.spnMaxBatchPieces.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.spnMaxBatchPieces.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.spnMaxBatchPieces.setMinimum(1)
        self.spnMaxBatchPieces.setMaximum(4)

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.spnMaxBatchPieces)

        self.label_22 = QLabel(self.groupBox_2)
        self.label_22.setObjectName(u"label_22")
        sizePolicy2.setHeightForWidth(self.label_22.sizePolicy().hasHeightForWidth())
        self.label_22.setSizePolicy(sizePolicy2)
        self.label_22.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_3.setWidget(2, QFormLayout.LabelRole, self.label_22)

        self.spnInitialSinglePieces = QSpinBox(self.groupBox_2)
        self.spnInitialSinglePieces.setObjectName(u"spnInitialSinglePieces")
        self.spnInitialSinglePieces.setMinimumSize(QSize(0, 0))
        self.spnInitialSinglePieces.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.spnInitialSinglePieces.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.spnInitialSinglePieces.setMinimum(5)
        self.spnInitialSinglePieces.setMaximum(20)

        self.formLayout_3.setWidget(2, QFormLayout.FieldRole, self.spnInitialSinglePieces)


        self.verticalLayout.addWidget(self.groupBox_2)

        self.groupBox_3 = QGroupBox(self.centralwidget)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.formLayout_4 = QFormLayout(self.groupBox_3)
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.label_13 = QLabel(self.groupBox_3)
        self.label_13.setObjectName(u"label_13")
        sizePolicy2.setHeightForWidth(self.label_13.sizePolicy().hasHeightForWidth())
        self.label_13.setSizePolicy(sizePolicy2)
        self.label_13.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_4.setWidget(0, QFormLayout.LabelRole, self.label_13)

        self.dspnInitialMinWeight = QDoubleSpinBox(self.groupBox_3)
        self.dspnInitialMinWeight.setObjectName(u"dspnInitialMinWeight")
        self.dspnInitialMinWeight.setMinimumSize(QSize(0, 0))
        self.dspnInitialMinWeight.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.dspnInitialMinWeight.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.dspnInitialMinWeight.setDecimals(2)
        self.dspnInitialMinWeight.setMinimum(0.020000000000000)
        self.dspnInitialMinWeight.setMaximum(100.000000000000000)
        self.dspnInitialMinWeight.setSingleStep(1.000000000000000)

        self.formLayout_4.setWidget(0, QFormLayout.FieldRole, self.dspnInitialMinWeight)

        self.label_7 = QLabel(self.groupBox_3)
        self.label_7.setObjectName(u"label_7")
        sizePolicy2.setHeightForWidth(self.label_7.sizePolicy().hasHeightForWidth())
        self.label_7.setSizePolicy(sizePolicy2)
        self.label_7.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_4.setWidget(1, QFormLayout.LabelRole, self.label_7)

        self.dspnStabilityThreshold = QDoubleSpinBox(self.groupBox_3)
        self.dspnStabilityThreshold.setObjectName(u"dspnStabilityThreshold")
        self.dspnStabilityThreshold.setMinimumSize(QSize(0, 0))
        self.dspnStabilityThreshold.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.dspnStabilityThreshold.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.dspnStabilityThreshold.setDecimals(2)
        self.dspnStabilityThreshold.setMinimum(0.020000000000000)
        self.dspnStabilityThreshold.setMaximum(1.000000000000000)
        self.dspnStabilityThreshold.setSingleStep(0.010000000000000)

        self.formLayout_4.setWidget(1, QFormLayout.FieldRole, self.dspnStabilityThreshold)

        self.label_19 = QLabel(self.groupBox_3)
        self.label_19.setObjectName(u"label_19")
        sizePolicy2.setHeightForWidth(self.label_19.sizePolicy().hasHeightForWidth())
        self.label_19.setSizePolicy(sizePolicy2)
        self.label_19.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_4.setWidget(2, QFormLayout.LabelRole, self.label_19)

        self.spnDecimalPlaces = QSpinBox(self.groupBox_3)
        self.spnDecimalPlaces.setObjectName(u"spnDecimalPlaces")
        self.spnDecimalPlaces.setMinimumSize(QSize(0, 0))
        self.spnDecimalPlaces.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.spnDecimalPlaces.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.spnDecimalPlaces.setMinimum(0)
        self.spnDecimalPlaces.setMaximum(4)
        self.spnDecimalPlaces.setValue(2)

        self.formLayout_4.setWidget(2, QFormLayout.FieldRole, self.spnDecimalPlaces)


        self.verticalLayout.addWidget(self.groupBox_3)

        self.groupBox_4 = QGroupBox(self.centralwidget)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.formLayout_5 = QFormLayout(self.groupBox_4)
        self.formLayout_5.setObjectName(u"formLayout_5")
        self.cbPort = QComboBox(self.groupBox_4)
        self.cbPort.setObjectName(u"cbPort")
        sizePolicy.setHeightForWidth(self.cbPort.sizePolicy().hasHeightForWidth())
        self.cbPort.setSizePolicy(sizePolicy)
        self.cbPort.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        self.formLayout_5.setWidget(0, QFormLayout.FieldRole, self.cbPort)

        self.cbBaudRate = QComboBox(self.groupBox_4)
        self.cbBaudRate.setObjectName(u"cbBaudRate")
        sizePolicy.setHeightForWidth(self.cbBaudRate.sizePolicy().hasHeightForWidth())
        self.cbBaudRate.setSizePolicy(sizePolicy)
        self.cbBaudRate.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        self.formLayout_5.setWidget(1, QFormLayout.FieldRole, self.cbBaudRate)

        self.label_23 = QLabel(self.groupBox_4)
        self.label_23.setObjectName(u"label_23")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.label_23.sizePolicy().hasHeightForWidth())
        self.label_23.setSizePolicy(sizePolicy3)
        self.label_23.setMinimumSize(QSize(75, 0))
        self.label_23.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_5.setWidget(0, QFormLayout.LabelRole, self.label_23)

        self.label_24 = QLabel(self.groupBox_4)
        self.label_24.setObjectName(u"label_24")
        sizePolicy3.setHeightForWidth(self.label_24.sizePolicy().hasHeightForWidth())
        self.label_24.setSizePolicy(sizePolicy3)
        self.label_24.setMinimumSize(QSize(75, 0))
        self.label_24.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_5.setWidget(1, QFormLayout.LabelRole, self.label_24)


        self.verticalLayout.addWidget(self.groupBox_4)

        self.btnSaveParams = QPushButton(self.centralwidget)
        self.btnSaveParams.setObjectName(u"btnSaveParams")
        self.btnSaveParams.setFont(font2)

        self.verticalLayout.addWidget(self.btnSaveParams)


        self.horizontalLayout_5.addLayout(self.verticalLayout)

        self.line_4 = QFrame(self.centralwidget)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.Shape.VLine)
        self.line_4.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout_5.addWidget(self.line_4)

        self.horizontalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer)

        self.rightPanel = QWidget(self.centralwidget)
        self.rightPanel.setObjectName(u"rightPanel")
        self.horizontalLayout_4 = QHBoxLayout(self.rightPanel)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.widget = QWidget(self.rightPanel)
        self.widget.setObjectName(u"widget")

        self.horizontalLayout_4.addWidget(self.widget)


        self.horizontalLayout_5.addWidget(self.rightPanel)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"<html><head/><body><p align=\"center\"><span style=\" font-size:26pt;\">\u8bbe\u7f6e</span></p><p align=\"center\"><span style=\" font-size:26pt;\">\u6570\u91cf</span></p></body></html>", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"<html><head/><body><p align=\"center\"><span style=\" font-size:26pt; color:#ff00ff;\">\u5b9e\u9645</span></p><p align=\"center\"><span style=\" font-size:26pt; color:#ff00ff;\">\u6570\u91cf</span></p></body></html>", None))
        self.lblTotalPieces.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"<html><head/><body><p align=\"center\"><span style=\" font-size:26pt; color:#5555ff;\">\u5b9e\u9645</span></p><p align=\"center\"><span style=\" font-size:26pt; color:#5555ff;\">\u91cd\u91cf</span></p></body></html>", None))
        self.lblActWeight.setText(QCoreApplication.translate("MainWindow", u"-----", None))
        self.btnStart.setText(QCoreApplication.translate("MainWindow", u"\u5f00\u59cb", None))
        self.btnStop.setText(QCoreApplication.translate("MainWindow", u"\u505c\u6b62", None))
        self.btnClear.setText(QCoreApplication.translate("MainWindow", u"\u6e05\u9664\u5f02\u5e38", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("MainWindow", u"\u5f3a\u5236\u6821\u51c6", None))
        self.label_20.setText(QCoreApplication.translate("MainWindow", u"\u6821\u51c6\u6570\u91cf:", None))
        self.btnForce.setText(QCoreApplication.translate("MainWindow", u"\u5f3a\u5236\u6821\u51c6", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"\u72b6\u6001\u4e0e\u91cd\u91cf", None))
        self.label_21.setText(QCoreApplication.translate("MainWindow", u"\u5f53\u524d\u72b6\u6001:", None))
        self.lblState.setText(QCoreApplication.translate("MainWindow", u"-----", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"\u91cd\u91cf\u53d8\u5316\u91cf:", None))
        self.lblDeltaWeight.setText(QCoreApplication.translate("MainWindow", u"0.00", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"\u5e73\u5747\u5355\u5f20\u91cd\u91cf:", None))
        self.lblAvgWeight.setText(QCoreApplication.translate("MainWindow", u"0.00", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"\u5355\u5f20\u4e0a\u9650\u91cd\u91cf:", None))
        self.lblTolHigh.setText(QCoreApplication.translate("MainWindow", u"0.00", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"\u5355\u5f20\u4e0b\u9650\u91cd\u91cf:", None))
        self.lblTolLow.setText(QCoreApplication.translate("MainWindow", u"0.00", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"\u4e0a\u6b21\u57fa\u51c6\u91cd\u91cf:", None))
        self.lblLastBaseWeight.setText(QCoreApplication.translate("MainWindow", u"0.00", None))
        self.label_15.setText(QCoreApplication.translate("MainWindow", u"\u4e0a\u6b21\u7a33\u5b9a\u91cd\u91cf:", None))
        self.lblLastStableWeight.setText(QCoreApplication.translate("MainWindow", u"0.00", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"\u91c7\u6837\u4e0e\u5224\u5b9a", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", u"\u5355\u5f20\u91cd\u91cf\u504f\u5dee:", None))
        self.dspnTolerancePercent.setSuffix(QCoreApplication.translate("MainWindow", u"%", None))
        self.label_18.setText(QCoreApplication.translate("MainWindow", u"\u5355\u6b21\u53d6\u653e\u6570\u91cf:", None))
        self.label_22.setText(QCoreApplication.translate("MainWindow", u"\u521d\u59cb\u5355\u7247\u6570\u91cf:", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindow", u"\u7cfb\u7edf\u7a33\u5b9a\u6027", None))
        self.label_13.setText(QCoreApplication.translate("MainWindow", u"\u6700\u5c0f\u8bc6\u522b\u91cd\u91cf:", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"\u7a33\u5b9a\u5224\u5b9a\u9608\u503c:", None))
        self.label_19.setText(QCoreApplication.translate("MainWindow", u"\u4eea\u8868\u5c0f\u6570\u4f4d\u6570:", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("MainWindow", u"\u4e32\u53e3\u8bbe\u7f6e", None))
        self.label_23.setText(QCoreApplication.translate("MainWindow", u"\u7f16\u53f7:", None))
        self.label_24.setText(QCoreApplication.translate("MainWindow", u"\u6ce2\u7279\u7387:", None))
        self.btnSaveParams.setText(QCoreApplication.translate("MainWindow", u"\u4fdd\u5b58\u914d\u7f6e", None))
    # retranslateUi

