import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox)
from PyQt5.QtCore import QThread, pyqtSignal
import boto3
import json

class LambdaInvoker(QThread):
    """
    Thread to invoke the Lambda function and emit the result.
    """
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, payload):
        super().__init__()
        self.payload = payload

    def run(self):
        try:
            lambda_client = boto3.client('lambda', region_name="us-east-1")
            response = lambda_client.invoke(
                FunctionName="example-lambda",
                InvocationType='RequestResponse',
                Payload=json.dumps(self.payload).encode('utf-8')
            )
            payload = json.loads(response['Payload'].read().decode('utf-8'))
            if payload.get('statusCode') not in [200, 201]:
                raise Exception(payload)
            else:
                payload_body = json.loads(payload.get('body'))
                result = f"Status Code: {payload.get('statusCode')}\n"
                result += f"Student Name: {payload_body.get('name')}\n"
                result += f"Career: {payload_body.get('career')}\n"
                result += f"College: {payload_body.get('college')}\n"
            self.result_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lambda Invoker (PyQt)")
        self.setGeometry(100, 100, 600, 400)  # Adjust size

        self.payload_label = QLabel("Data:")
        self.name_edit = QLineEdit()
        self.name_edit.setText('student_name')
        self.career_edit = QLineEdit()
        self.career_edit.setText('student_career')
        self.college_edit = QLineEdit()
        self.college_edit.setText('student_college')

        self.operation_type_label = QLabel("Operation Type:")
        self.operation_type = QComboBox()
        self.operation_type.addItem('GET')
        self.operation_type.addItem('PUT')
        self.operation_type.addItem('POST')
        if self.operation_type.currentText() == 'GET':
            self.career_edit.hide()
            self.college_edit.hide()
        else:
            self.career_edit.show()
            self.college_edit.show()

        self.operation_type.currentIndexChanged.connect(self.switch_layout)

        self.invoke_button = QPushButton("Invoke Lambda")
        self.result_text = QTextEdit()
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)

        self.invoke_button.clicked.connect(self.invoke_lambda)
        
        # Layout

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.operation_type_label)
        main_layout.addWidget(self.operation_type)  
        main_layout.addWidget(self.payload_label)
        main_layout.addWidget(self.name_edit)
        main_layout.addWidget(self.career_edit)
        main_layout.addWidget(self.college_edit)
        main_layout.addWidget(self.payload_label)
        main_layout.addWidget(self.name_edit)
        main_layout.addWidget(self.invoke_button)
        main_layout.addWidget(self.result_text)
        main_layout.addWidget(self.error_text)
    
        self.setLayout(main_layout)

    def invoke_lambda(self):
        payload = {
            "httpMethod": self.operation_type.currentText(),
            "data": {
                "name": self.name_edit.text(),
                "career": self.career_edit.text(),
                "college": self.college_edit.text()
            }
        }

        self.result_text.clear()
        self.error_text.clear()

        self.invoker_thread = LambdaInvoker(payload)
        self.invoker_thread.result_signal.connect(self.handle_result)
        self.invoker_thread.error_signal.connect(self.handle_error)
        self.invoker_thread.start()

    def handle_result(self, result):
        self.result_text.setText(result)

    def handle_error(self, error):
        self.error_text.setText(error)

    def switch_layout(self):
        if self.operation_type.currentText() == 'GET':
            self.career_edit.hide()
            self.college_edit.hide()
        else:
            self.career_edit.show()
            self.college_edit.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())