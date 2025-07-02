
from betterhtmlchunking import DomRepresentation
from betterhtmlchunking.main import ReprLengthComparisionBy
from betterhtmlchunking.main import tag_list_to_filter_out

import os
class HTMLChunker:
    def __init__(self, html_content=""):
        self.html_content = html_content
        self.max_chunk_size = 18000  # Default chunk size, can be adjusted later
        self.min_chunk_size = 3000  # Minimum chunk size for DOM tree chunking


    def set_html_content(self, html_content):
        self.html_content = html_content
    
    
    def simple_chunkify_pages(self,docs):
        chunk_size = self.max_chunk_size
       
        chunks = []
        for page in docs:
            for i in range(0, len(page), chunk_size):
                chunk = page[i:i+chunk_size]
                chunks.append(chunk)
            
        print("created:", len(chunks), "chunks from docs")
        print("Chunks", chunks)
        return chunks
    
    
    def DOM_tree_chunkify(self,html_content=None):
        chunks = []
        min_chunk_size = self.min_chunk_size
        max_chunk_size = self.max_chunk_size
        current_chunk = ""
        dom_repr = DomRepresentation(
            MAX_NODE_REPR_LENGTH=max_chunk_size,
            website_code=html_content,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )
        dom_repr.compute_tree_representation()
        dom_repr.compute_tree_regions_system()
        dom_repr.compute_render_system()
        #self.render_html(dom_repr)
        for idx in dom_repr.tree_regions_system.sorted_roi_by_pos_xpath:
            roi_html_render: str = \
                dom_repr.render_system.get_roi_html_render_with_pos_xpath(
                    roi_idx=idx
                )
            if len(current_chunk) + len(roi_html_render) < min_chunk_size:
                current_chunk += roi_html_render
            elif len(current_chunk) + len(roi_html_render) <= max_chunk_size:
                current_chunk += roi_html_render
                chunks.append(current_chunk)
                current_chunk = ""
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = roi_html_render
        # Add any remaining chunk
        if current_chunk:
            chunks.append(current_chunk)
        print("created:", len(chunks), "chunks from DOM tree")
        
        return chunks

    def render_html(self, dom_repr):
        # Render HTML:
        for idx in dom_repr.tree_regions_system.sorted_roi_by_pos_xpath:
            print("*" * 50)
            print(f"IDX: {idx}")
            roi_html_render: str =\
                dom_repr.render_system.get_roi_html_render_with_pos_xpath(
                    roi_idx=idx
                )
            print(roi_html_render)
        
    def print_chunks(self, chunks):
        for idx, chunk in enumerate(chunks):
            print(f"Chunk {idx + 1}:\n{chunk}\n\n{'-' * 80}")
    
    def load_test_data(self):
        docs = []
        base_dir = os.path.dirname(__file__)
        with open(os.path.join(base_dir, "scoped_page_0.html"), "r", encoding="utf-8") as file:
            docs.append(file.read())

        with open(os.path.join(base_dir, "scoped_page_1.html"), "r", encoding="utf-8") as file:
            docs.append(file.read())
        with open(os.path.join(base_dir, "scoped_page_2.html"), "r", encoding="utf-8") as file:
            docs.append(file.read())
        with open(os.path.join(base_dir, "scoped_page_3.html"), "r", encoding="utf-8") as file:
            docs.append(file.read())
          # Set the first document as the html_content
        print(f"Loaded {len(docs)} pages of HTML content.")
        return docs


