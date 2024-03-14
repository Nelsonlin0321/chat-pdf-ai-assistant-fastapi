from pypdf import PdfReader
from textblob import TextBlob
import nltk
nltk_download_dir = "/tmp/nltk_data"
nltk.data.path.append(nltk_download_dir)


def parse_pdf(file_path):

    nltk.download('punkt', download_dir=nltk_download_dir)

    reader = PdfReader(file_path)
    full_text = ""
    page_sentence_list = []
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text().strip()
        full_text += "\n"+text
        blob = TextBlob(text)

        for sentence in blob.sentences:
            tmp_dict = {}
            tmp_dict["page_number"] = page_num
            tmp_dict["sentence"] = sentence
            page_sentence_list.append(tmp_dict)

    return full_text, page_sentence_list


def merge_sentences_to_chunks(page_sentence_list, sentence_size=128, overlapping_num=3):

    chunks = []
    accumulate_len = 0
    sentence_sizes = []
    windows_sentences = []
    windows_page_numbers = []

    chunk_id = 0
    for item in page_sentence_list:

        page_number = item["page_number"]
        sentence = item["sentence"]

        word_len = len(sentence.words)
        if accumulate_len+word_len <= sentence_size or len(windows_sentences) == 0:
            windows_sentences.append(str(sentence))
            windows_page_numbers.append(page_number)
            accumulate_len += word_len
            sentence_sizes.append(word_len)

        else:
            windows_context = "\n".join(windows_sentences)
            chunks.append({"text": windows_context,
                          "page_number": list(set(windows_page_numbers)),
                           "word_size": accumulate_len,
                           "chunk_id": chunk_id
                           }
                          )
            # initialize
            chunk_id += 1
            windows_sentences = windows_sentences[-overlapping_num:].copy()+[
                str(sentence)]
            windows_page_numbers = windows_page_numbers[-overlapping_num:].copy()+[
                page_number]
            accumulate_len = sum(sentence_sizes[-overlapping_num:]) + word_len

    if len(windows_sentences) > 0:
        windows_context = "\n".join(windows_sentences)
        chunks.append({"text": windows_context,
                      "page_number": list(set(windows_page_numbers)),
                       "word_size": accumulate_len,
                       "chunk_id": chunk_id
                       })

    return chunks
