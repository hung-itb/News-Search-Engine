
import os, py_vncorenlp, json
from datetime import datetime
dirname = os.path.dirname(__file__)

class file_utils:
    @staticmethod
    def read_file(abs_path = None, default = None, encoding = None):
        if not os.path.exists(abs_path):
            if default is not None:
                return default
            else:
                raise Exception('File not found:', abs_path)
        f = open(abs_path, encoding=encoding)
        data = f.read()
        f.close()
        return data
    @staticmethod
    def write_file(abs_path = None, content = '', append = False):
        if append and os.path.exists(abs_path):
            f = open(abs_path, 'a')
        else:
            if not os.path.exists(os.path.dirname(abs_path)):
                os.makedirs(os.path.dirname(abs_path))
            f = open(abs_path, 'w')
        f.write(content)
        f.close()
    @staticmethod
    def delete_file(abs_path = None):
        if os.path.exists(abs_path):
            os.remove(abs_path)

class storage:
    filepath = os.path.join(dirname, 'data', 'storage.txt')
    storage = json.loads(file_utils.read_file(filepath, '{}'))
    storage_temp = {}
    @staticmethod
    def get(key, default = None):
        temp_result = storage.storage_temp.get(key, None)
        if temp_result is None: return storage.storage.get(key, default)
        return temp_result
    @staticmethod
    def set(key, value):
        storage.storage[key] = value
        file_utils.write_file(storage.filepath, json.dumps(storage.storage, indent=2))
    @staticmethod
    def set_temp(key, value):
        storage.storage_temp[key] = value
    @staticmethod
    def delete(key):
        storage.storage.pop(key, None)
        file_utils.write_file(storage.filepath, json.dumps(storage.storage, indent=2))
    @staticmethod
    def delete_temp(key):
        storage.storage_temp.pop(key, None)

class datetime_utils:
    valid_chars_in_date = set('0123456789/') # Các ký tự hợp lệ được xuất hiện trong chuỗi ngày tháng
    valid_if_in_head = set('.,!?:;') # Các ký tự không hợp lệ trong chuỗi ngày tháng, nhưng nếu đứng đầu chuỗi thì vẫn hợp lệ. Dùng thêm cái này vì chuỗi ngày tháng truyền vào chưa xử lý gọn gàng
    must_exist_in_date = set('/') # Các ký mà một chuỗi ngày tháng nào đó bắt buộc phải chứa
    is_day = lambda i: 1 <= i <= 31
    is_month = lambda i: 1 <= i <= 12
    is_year = lambda i: 1900 <= i <= 2100

    @staticmethod
    def to_date(s: str, prev = None, year = None):
        """
            Format chuỗi ngày tháng bất kỳ về dạng chuẩn, đồng nhất.
            Nếu chuỗi truyền vào không hợp lệ, trả về 0
            s: Chuỗi cần chuyển
            prev: Tiền tố đứng trước chuỗi s trong câu
            year: Năm được bù vào chuỗi nếu s chỉ bao gồm ngày và tháng
        """
        if not s or s == '': return 0
        if s[0] in datetime_utils.valid_if_in_head: s = s[1:]
        if s == '': return 0
        if s[-1] in datetime_utils.valid_if_in_head: s = s[:-1]
        sep_char = None
        for c in s:
            if c not in datetime_utils.valid_chars_in_date: return 0
            if c in datetime_utils.must_exist_in_date:
                if sep_char is None:
                    sep_char = c
                elif sep_char != c:
                    return 0
        if not sep_char: return 0
        parts = s.split(sep_char)
        for part in parts:
            if part == '': return 0
        num_parts = len(parts)
        if num_parts == 1 or num_parts > 3: return 0
        v = [int(i) for i in parts]
        if num_parts == 2:
            if datetime_utils.is_day(v[0]) and datetime_utils.is_month(v[1]):
                if prev in ['ngày', 'từ', 'đến', 'tối', 'hôm', 'sáng']: return f'{v[0]}/{v[1]}/{year}'
                return 0
            elif datetime_utils.is_month(v[0]) and datetime_utils.is_year(v[1]):
                return f'{v[0]}/{v[1]}'
            return 0
        if datetime_utils.is_day(v[0]) and datetime_utils.is_month(v[1]) and datetime_utils.is_year(v[2]): return f'{v[0]}/{v[1]}/{v[2]}'
        return 0
    
    @staticmethod
    def extract_dates(s, year = None):
        """
            Trích xuất tất cả các chuỗi ngày tháng trong một chuỗi dài, trả về
            ánh xạ từ chuỗi ngày tháng sang dạng chuẩn của nó
        """
        s = string_utils.remove_not_allowed_letter_and_convert_to_lowercase(s)
        if not year: year = datetime.now().year
        ws = s.split(' ')
        r = {}
        for i, w in enumerate(ws):
            date = datetime_utils.to_date(w, ws[i-1] if i != 0 else None, year)
            if date: r[w] = date
        return r

class string_utils:
    allowed_letters_list = ' '.join(['a ă â b c d đ e ê g h i j k l m n o ô ơ p q r s t u ư v x y z w',
        'A Ă Â B C D Đ E Ê G H I J K L M N O Ô Ơ P Q R S T U Ư V X Y Z W',
        '0123456789',
        'à á ạ ả ã â ầ ấ ậ ẩ ẫ ă ằ ắ ặ ẳ ẵ',
        'è é ẹ ẻ ẽ ê ề ế ệ ể ễ',
        'ì í ị ỉ ĩ',
        'ò ó ọ ỏ õ ô ồ ố ộ ổ ỗ ơ ờ ớ ợ ở ỡ',
        'ù ú ụ ủ ũ ư ừ ứ ự ử ữ',
        'ỳ ý ỵ ỷ ỹ',
        'À Á Ạ Ả Ã Â Ầ Ấ Ậ Ẩ Ẫ Ă Ằ Ắ Ặ Ẳ Ẵ',
        'È É Ẹ Ẻ Ẽ Ê Ề Ế Ệ Ể Ễ',
        'Ì Í Ị Ỉ Ĩ',
        'Ò Ó Ọ Ỏ Õ Ô Ồ Ố Ộ Ổ Ỗ Ơ Ờ Ớ Ợ Ở Ỡ',
        'Ù Ú Ụ Ủ Ũ Ư Ừ Ứ Ự Ử Ữ',
        'Ỳ Ý Ỵ Ỷ Ỹ'
    ])
    allowed_letters_strict = set(allowed_letters_list) # Tập các chữ cái hợp lệ, không chứa các dấu đặc biệt
    allowed_letters = set(allowed_letters_list).union('- / , .') # Tập các chữ cái hợp lệ, có chứa các dấu đặc biệt
    
    @staticmethod
    def remove_not_allowed_letter_and_convert_to_lowercase(t: str, strict = False):
        """
            Xóa bỏ tất cả các ký tự không hợp lệ trong một chuỗi, thường xuất hiện đối với các chuỗi được thu thập từ Internet.
            Sau đó sẽ chuyển chuỗi về chữ thường
            t: Chuỗi cần chuyển đổi
            strict: Có nghiêm ngặt về các ký tự hợp lệ hay không. Nếu đúng thì một vài ký tự nối câu,
            nối từ, các dấu trong phép toán,... sẽ không xuất hiện
        """
        allowed_letters_2 = string_utils.allowed_letters_strict if strict else string_utils.allowed_letters
        if t is None: return None
        t = t.lower()
        chars = set(t)
        for char in chars:
            if char not in allowed_letters_2: t = t.replace(char, ' ')
        while '  ' in t: t = t.replace('  ', ' ')
        return t.strip()

    rdrsegmenter = py_vncorenlp.VnCoreNLP(annotators=["wseg"], save_dir=os.path.join(dirname, 'VnCoreNLP'))
    stop_words = set(pharse.replace(' ', '_') for pharse in file_utils.read_file(os.path.join(dirname, 'vietnamese-stopwords.txt'), '', 'utf-8').split('\n'))
    @staticmethod
    def tokenize_vncore_nlp(text, strict = True):
        rdrsegmenter = string_utils.rdrsegmenter
        text = string_utils.remove_not_allowed_letter_and_convert_to_lowercase(text, strict)
        output = rdrsegmenter.word_segment(text)
        result = []
        for s in output:
            for t in s.split(' '):
                if t in string_utils.stop_words: continue
                result.append(t)
        return result

def prepare_doc_for_solr(doc):
    doc['abstract'] = doc.get('description') or ''
    doc['created_date'] = doc['created-at'].split(',')[1].strip() if 'created-at' in doc else '1/1/2020'
    d, m, y = [int(i) for i in doc['created_date'].split('/')]
    doc['created_date'] = f'{d}/{m}/{y}'
    doc['num_days_from_1990_to_created_date'] = str((datetime(y, m, d) - datetime(1990, 1, 1)).days)
    category = (doc.get('category-tree') or '').split('/')[0].replace(' ', '_')
    if category != '':
        doc['category'] = category
    doc.pop('category-tree', None)
    doc.pop('author', None)
    doc.pop('id', None)
    doc.pop('description', None)
    doc.pop('created-at', None)

    content_keys = ['title', 'abstract', 'content']
    for key in content_keys:
        if key != 'content': doc[key + '_original'] = doc.get(key) or ''
        extracted_dates = datetime_utils.extract_dates(doc.get(key) or '', doc['created_date'].split('/')[2])
        for original_value, date in extracted_dates.items():
            doc[key] = doc[key].replace(original_value, date)
    for key in content_keys:
        doc[key] = ' '.join(string_utils.tokenize_vncore_nlp(doc.get(key) or '', False))
        for s in ['-_', '_-', ',_', '_,', '_.', '._']:
            doc[key] = doc[key].replace(s, '')

    return doc
