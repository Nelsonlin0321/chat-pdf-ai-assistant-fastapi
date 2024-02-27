
from . import pdf_utils
from .vertex_ai import TextEmbedding
import os


class PDFParser():
    def __init__(self, embedding_model: TextEmbedding, sentence_size=128, overlapping_num=3) -> None:
        self.sentence_size = sentence_size
        self.overlapping_num = overlapping_num
        self.embedding_model = embedding_model

    def parse(self, file_path):
        file_name = os.path.basename(file_path)
        page_sentence_list = pdf_utils.parse_pdf(file_path)

        chunk_metas = pdf_utils.merge_sentences_to_chunks(
            page_sentence_list,
            sentence_size=self.sentence_size,
            overlapping_num=self.overlapping_num)

        chunks = []
        for metas in chunk_metas:
            metas['file_name'] = file_name
            chunks.append(metas['text'])

        embeddings = self.embedding_model(sentences=chunks)
        for embedding, metas in zip(embeddings, chunk_metas):
            metas['embedding'] = embedding

        return embedding
