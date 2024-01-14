import streamlit as st
import requests
import json
from openai import AzureOpenAI
import time
import os
import traceback
import sys
import sqlite3
from dotenv import load_dotenv
from datetime import datetime

from src.utils.gpt_trigger_function import build_filter_query
from src.utils.csv_builder import create_temp_csv_file
from src.utils.chat_on_demand import chat_on_demand
from src.utils.load_prompts import load_prompts
from src.utils.google_sheet import read_data, update_data
from src.utils.telegram import send_message

if 'current_query' not in st.session_state:
    st.session_state['current_query'] = None

# if 'remain_laptops' not in st.session_state:
#     st.session_state['remain_laptops'] = None

# if 'current_laptops' not in st.session_state:
#     st.session_state['current_laptops'] = None

# if 'show_form' not in st.session_state:
#     st.session_state['show_form'] = False


load_dotenv(override=True)


def __submit_user_data():
    # Get all data in sidebar
    data = {}

    # Get the last ID
    data['STT'] = read_data().iloc[-1]['STT'] + 1
    data['Họ và Tên'] = st.session_state.get('user_name', '')
    data['Số điện thoại'] = st.session_state.get('user_phone', '')
    data['Email'] = st.session_state.get('user_email', '')
    data['Môn học đề xuất mở thêm (Dự kiến)'] = st.session_state.get(
        'user_subject', '')
    data['Mã môn học'] = st.session_state.get('user_subject_id', '')
    data['Lí do mở thêm'] = st.session_state.get('user_reason', '')

    data['STT'] = int(data['STT'])

    print(data)

    with st.spinner('Đang viết dữ liệu vào Google Sheet ...'):
        # Update the data
        update_data(data)

        # Send message to telegram
        send_message(data)

    msg = 'Đã gửi thông tin thành công, nhà trường sẽ liên hệ với bạn trong thời gian sớm nhất !'
    st.session_state.messages.append(
        {'role': 'assistant', 'content': msg}
    )
    _type_writer(msg, speed=40)

    # Thank you for using the chatbot
    msg = 'Em cảm ơn anh/chị đã sử dụng dịch vụ tư vấn của BKchat ạ'
    st.session_state.messages.append(
        {'role': 'assistant', 'content': msg}
    )
    _type_writer(msg, speed=40)

    st.balloons()

    st.session_state['show_form'] = False


def __store_user_requirement(content: str) -> None:
    st.session_state['user_requirement'] = content

##################### Sidebar to leave contact info #####################


if st.session_state['show_form']:
    # Create in sidebar
    st.sidebar.subheader('Thông tin sinh viên')
    user_name = st.sidebar.text_input(label='Họ và tên', key='input_user_name')
    phone_num = st.sidebar.text_input(
        label='Số điện thoại', key='input_user_phone')
    email = st.sidebar.text_input(label='Email', key='input_user_email')
    user_subject = st.sidebar.text_input(
        label='Môn học đề xuất mở thêm (Dự kiến)', key='input_user_subject')
    user_subject_id = st.sidebar.text_input(
        label='Mã môn học', key='input_user_subject_id')
    reason = st.sidebar.text_input(
        label='Lí do mở thêm', key='input_user_reason')

    if user_name:
        st.session_state.user_name = user_name

    if phone_num:
        st.session_state.user_phone = phone_num

    if email:
        st.session_state.user_email = email

    if user_subject:
        st.session_state.user_subject = user_subject

    if user_subject_id:
        st.session_state.user_time = user_subject_id

    if reason:
        st.session_state.user_reason = reason

    # Submit button
    submit = st.sidebar.button(
        label='Gửi thông tin', key='submit', on_click=__submit_user_data)


##################### Function to calculate the current message context #####################

def queries_db(**kwargs):
    print('==========> Running queries_db function')

    # Calculate the current context, if it is greater than 85% of the total context, then release the context
    current_token = current_context_calculator()

    if current_token >= int(16000 * 85 / 100):
        # Release the context
        release_context_token()

    # First, release the current query and remain laptops
    st.session_state.current_query = None
    st.session_state.remain_laptops = None

    st.session_state.messages.append(
        {"role": "system", "content": "Người dùng đang muốn tìm kiếm môn học với các tiêu chí như sau"}
    )

    # Next, store the user requirement
    __store_user_requirement(kwargs.get('content', ''))

    max_retry = 5
    while max_retry > 0:
        conn = sqlite3.connect('database/2022-2.db')
        try:
            query = build_filter_query(**kwargs)

            with st.spinner('Thinking ...'):
                remind_query = chat_on_demand(messages=[
                    {"role": "system", "content": f"Bạn nhắc lại 1 chút về các tiêu chí bộ lọc mà bạn đã lựa chọn: {query} và giải thích vì sao bạn lại chọn nó cho người dùng hiểu. Sau khi giải thích xong, nhớ nói câu: Tiếp theo, mình sẽ tìm trên cơ sở dữ liệu từ những tiêu chí này"}
                ])

            st.session_state.messages.append(
                {"role": "system", "content": remind_query}
            )

            st.session_state.conversation.append(
                {"role": "system", "content": remind_query}
            )

            _type_writer(remind_query, speed=100)

            st.session_state.messages.append(
                {"role": "system", "content": f'Đang thực hiện truy vấn: {query}'}
            )
            st.session_state.conversation.append(
                {"role": "system", "content": f'Đang thực hiện truy vấn: {query}'}
            )
            print(f'==========> Query: {query}')
            query_result = conn.execute(query).fetchall()
        except Exception as e:
            print(traceback.format_exc())
            st.error('Đã xảy ra lỗi khi truy vấn CSDL, đang thử lại')
            max_retry -= 1
            time.sleep(1)
        else:
            conn.close()
            break

    if max_retry == 0:
        st.error('Đã xảy ra lỗi khi truy vấn CSDL, vui lòng khởi động lại')
        st.stop()

    headers = []

    query = ''

    filename = 'current_query.csv'

    csv_path = create_temp_csv_file(headers, query, filename)

    if not csv_path:
        st.error('Đã xảy ra lỗi khi tạo file csv, vui lòng thử lại')
        st.session_state.query_result = None
    else:
        st.session_state.query_result = csv_path

    if len(query_result) == 0:
        st.session_state.conversation.append(
            {"role": "assistant",
                "content": "Ui, hiện tại không có laptop nào phù hợp với yêu cầu của bạn rồi. Bạn có thể thay đổi cấu hình hoặc các thông số 1 chút (ví dụ như thay đổi mức giá, thay đổi dung lượng RAM, thay đổi dung lượng ổ cứng,...) để mình tìm kiếm lại nhé"}
        )

        st.chat_message("assistant").write(
            "Ui, hiện tại không có laptop nào phù hợp với yêu cầu của bạn rồi. Bạn có thể thay đổi cấu hình hoặc các thông số 1 chút (ví dụ như thay đổi mức giá, thay đổi dung lượng RAM, thay đổi dung lượng ổ cứng,...) để mình tìm kiếm lại nhé")
    else:
        st.session_state.messages.append(
            {"role": "assistant",
                "content": f"Đã tìm thấy {len(query_result)} laptop phù hợp với yêu cầu của bạn, trước tiên mình giới thiệu qua 5 mẫu laptop phù hợp nhất nhé"}
        )
        st.session_state.conversation.append(
            {"role": "assistant",
                "content": f"Đã tìm thấy {len(query_result)} laptop phù hợp với yêu cầu của bạn, trước tiên mình giới thiệu qua 5 mẫu laptop phù hợp nhất nhé"}
        )
        st.chat_message("assistant").write(
            f"Đã tìm thấy {len(query_result)} laptop phù hợp với yêu cầu của bạn, trước tiên mình giới thiệu qua 5 mẫu laptop phù hợp nhất nhé")

        # Now send the query result to the chatbot
        with open(csv_path, 'r', encoding='utf-8') as f:
            csv_content = f.read().split('\n')

        # Just send the first 5 rows ~ 5 laptops. The remaining will be store in the session state
        header = csv_content[0]
        send_content = '\n'.join(csv_content[1:5])
        remain_content = '\n'.join(csv_content[5:])

        st.session_state.remain_laptops = header + '\n' + remain_content
        st.session_state.current_laptops = header + '\n' + send_content

        st.session_state.messages.append(
            {"role": "system", "content": f'Đây là kết quả mới nhất gồm những laptop phù hợp với tiêu chí người dùng chọn ra. Hãy ghi nhớ nó để tư vấn thật nhiệt tình cho người dùng nhé\n {st.session_state.current_laptops}'}
        )

        st.session_state.messages.append(
            {"role": "system", "content": load_prompts(
                'system_guide_preview_query')}
        )
        with st.spinner('Thinking ...'):
            message = chat_on_demand(
                messages=st.session_state.messages
            )

        st.session_state.conversation.append(
            {"role": "assistant", "content": message}
        )
        st.session_state.messages.append(
            {"role": "assistant", "content": message}
        )

        _type_writer(message, speed=100)


def current_context_calculator() -> int:
    text = ''
    for msg in st.session_state.messages:
        text += msg['content']

    tokens: int = (len(text) % 16000) // 4

    return tokens

##################### Function to pseudo type writer smoothly #####################


def _type_writer(text: str, speed: int = 100) -> None:
    if text is None or text == '':
        return
    tokens = text
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = tokens[:index]
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

##################### Function to trigger event #####################


def release_context_token() -> None:
    """
        This function will keep the last answer of the chatbot and user to release the context token.
    """
    if st.session_state.remain_laptops:

        # Continue get max 5 laptops
        header = st.session_state.remain_laptops.split('\n')[0]
        send_content = '\n'.join(
            st.session_state.remain_laptops.split('\n')[1:5])
        remain_content = '\n'.join(
            st.session_state.remain_laptops.split('\n')[5:])

        st.session_state.remain_laptops = header + '\n' + remain_content

        # Blank the message
        st.session_state.messages = []

        # Load system guide
        st.session_state.messages.append(
            {"role": "system", "content": load_prompts(
                'system_guide_preview_query')}
        )
        st.session_state.conversation.append(
            {"role": "system", "content": load_prompts(
                'system_guide_preview_query')}
        )

        st.session_state.messages.append(
            {"role": "system", "content": f'Đây là kết quả mới nhất gồm những laptop phù hợp với tiêu chí người dùng chọn ra. Hãy ghi nhớ nó để tư vấn thật nhiệt tình cho người dùng nhé\n {header}\n{send_content}'}
        )
        st.session_state.conversation.append(
            {"role": "system", "content": f'Đây là kết quả mới nhất gồm những laptop phù hợp với tiêu chí người dùng chọn ra. Hãy ghi nhớ nó để tư vấn thật nhiệt tình cho người dùng nhé\n {header}\n{send_content}'}
        )

    else:
        header = ''
        send_content = ''
        remain_content = ''

    # Keep last answer
    last_answer = st.session_state.messages[-1]

    # Add last answer
    st.session_state.messages.append(
        {"role": "system", "content": f'Đây là câu nói/ câu hỏi cuối cùng của người dùng. Hãy tiếp tục trả lời nó: {last_answer}'}
    )
    st.session_state.conversation.append(
        {"role": "system", "content": f'Đây là câu nói/ câu hỏi cuối cùng của người dùng. Hãy tiếp tục trả lời nó: {last_answer}'}
    )

    with st.spinner('Thinking ...'):
        message = chat_on_demand(
            messages=st.session_state.messages
        )


class ChatGUI():

    with open('config/bot.json', 'r', encoding='utf-8') as f:
        BOT_CONFIG = json.load(f)

    with open('config/function_description.json', 'r', encoding='utf-8') as f:
        FUNCTION_DESCRIPTION = json.load(f)

    date = datetime.now().strftime("%d/%m/%Y")

    def __init__(self) -> None:

        self._init_session_state()
        self._init_sidebar()
        self._init_chatui()

        load_dotenv()

        # Init OpenAI Client
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2023-05-15",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

        # Init message event
        self._message_event()

    def trigger_function(self, status: bool = False, func_name: str = '', args: dict = {}) -> None:
        """
        Trigger the function in the backend
        For example: if status is True, and func_name is queries_db
        then run queries_db(*args)
        Args:
            func_name (str): name of function
            args (dict): 
            {
                'arg1': value1,
                'arg2': value2,
            }
        """

        if status:
            if func_name in globals() and callable(globals()[func_name]):
                if args != {}:
                    globals()[func_name](**args)
                else:
                    globals()[func_name]()

    # --------------------------- Function for init --------------------------- #

    def _init_session_state(self) -> None:
        if "messages" not in st.session_state:
            st.session_state["messages"] = [
                {"role": "system", "content": load_prompts('system_init')},
                {"role": "assistant", "content": load_prompts(
                    'assistant_init')}
            ]

        if "conversation" not in st.session_state:
            st.session_state["conversation"] = [
                {"role": "system", "content": load_prompts('system_init')},
                {"role": "assistant", "content": load_prompts(
                    'assistant_init')}
            ]

    def _init_sidebar(self) -> None:
        pass

    def _init_chatui(self) -> None:
        st.title("💬BKChat - Wish u have a good semester")
        st.caption(f"🚀 Dữ liệu về tkb được cập nhật đến ngày {self.date}")

        # Load message history of session into chat message
        for msg in st.session_state.conversation:
            if msg['role'] != 'system':
                st.chat_message(msg["role"]).write(msg["content"])

    def _refresh_role(self) -> None:
        current_token = current_context_calculator()

        print(f'Current tokens in context: {current_token}')

        if current_token >= int(16000 * 85 / 100):
            # Release the context
            release_context_token()

            st.session_state.messages.append(
                {'role': 'system', 'content': load_prompts('system_init')}
            )

            print('==========> Mission refreshed for chatbot to remember its role !')

    def _get_response(self) -> str:
        max_retry = 5

        while max_retry > 0:
            try:
                self._refresh_role()
                response = self.client.chat.completions.create(
                    model="GPT35TURBO16K",
                    messages=st.session_state.messages,
                    timeout=30,
                    max_tokens=4096,
                    temperature=1,
                    # function_call='auto',
                    # functions=self.FUNCTION_DESCRIPTION
                )

                return response
            except Exception as e:
                print(traceback.format_exc())
                st.error('Đã xảy ra lỗi khi gửi request đến OpenAI, đang thử lại')
                max_retry -= 1
                time.sleep(2)

        if max_retry == 0:
            st.error(
                'Đã xảy ra lỗi khi gửi request đến OpenAI, vui lòng khởi động lại')
            st.stop()

    def _message_event(self) -> None:
        if prompt := st.chat_input():
            if st.session_state.current_query:
                with open(st.session_state.current_query, 'r', encoding='utf-8') as f:
                    query = f.read()
                st.session_state.messages.append(
                    {"role": "system", "content": load_prompts(
                        'system_recal_current_query') + '\n' + query}
                )

            st.session_state.messages.append(
                {"role": "user", "content": prompt})
            st.session_state.conversation.append(
                {"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            with st.spinner("Thinking..."):
                response = self._get_response()
                answer = response.choices[0].message

            if answer.function_call:
                print(
                    f'==========> Function call: {answer.function_call.name}')
                self.trigger_function(
                    status=True,
                    func_name=answer.function_call.name,
                    args=json.loads(answer.function_call.arguments)
                )
            else:
                _type_writer(answer.content)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response.choices[0].message.content})
                st.session_state.conversation.append(
                    {"role": "assistant", "content": response.choices[0].message.content})


if __name__ == "__main__":
    chat = ChatGUI()
