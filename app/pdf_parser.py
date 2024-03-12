
from . import pdf_utils
# from .vertex_ai import TextEmbedding
import os


class PDFParser():
    def __init__(self, sentence_size=256, overlapping_num=3) -> None:
        self.sentence_size = sentence_size
        self.overlapping_num = overlapping_num

    def parse(self, file_path):

        file_name = os.path.basename(file_path)
        full_text, page_sentence_list = pdf_utils.parse_pdf(file_path)

        chunk_metas = pdf_utils.merge_sentences_to_chunks(
            page_sentence_list,
            sentence_size=self.sentence_size,
            overlapping_num=self.overlapping_num)

        for metas in chunk_metas:
            metas["file_name"] = file_name

        # chunks = []
        # for metas in chunk_metas:
        #     chunks.append(metas['text'])

        # embeddings = self.embedding_model(sentences=chunks)
        # for embedding, metas in zip(embeddings, chunk_metas):
        #     metas['embedding'] = embedding

        # {"text": str,
        #  "page_number": List[int],
        #  "word_size": int,
        #  "chunk_id": int,
        #  "embedding": List[List[float]]
        #  }

        return full_text, chunk_metas
