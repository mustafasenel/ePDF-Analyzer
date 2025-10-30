"""PDF reading and text extraction using PyMuPDF (fitz)"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from config.settings import settings


class PDFReaderError(Exception):
    """PDF reading error"""
    pass


class PDFReader:
    """
    PDF reader using PyMuPDF for text extraction and metadata
    """
    
    def __init__(self, pdf_path: str | Path):
        """
        Initialize PDF reader
        
        Args:
            pdf_path: Path to PDF file
        """
        self.pdf_path = Path(pdf_path)
        self.doc: Optional[fitz.Document] = None
        
        if not self.pdf_path.exists():
            raise PDFReaderError(f"PDF file not found: {pdf_path}")
    
    def __enter__(self):
        """Context manager entry"""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def open(self) -> None:
        """Open the PDF document"""
        try:
            self.doc = fitz.open(self.pdf_path)
        except Exception as e:
            raise PDFReaderError(f"Failed to open PDF: {str(e)}")
    
    def close(self) -> None:
        """Close the PDF document"""
        if self.doc:
            self.doc.close()
            self.doc = None
    
    def get_page_count(self) -> int:
        """
        Get total number of pages
        
        Returns:
            Number of pages
        """
        if not self.doc:
            raise PDFReaderError("PDF not opened. Call open() first.")
        return len(self.doc)
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Extract PDF metadata
        
        Returns:
            Dictionary containing metadata
        """
        if not self.doc:
            raise PDFReaderError("PDF not opened. Call open() first.")
        
        metadata = self.doc.metadata
        file_size = self.pdf_path.stat().st_size
        
        # Format dates if present
        creation_date = self._format_pdf_date(metadata.get('creationDate'))
        mod_date = self._format_pdf_date(metadata.get('modDate'))
        
        return {
            "title": metadata.get('title') or None,
            "author": metadata.get('author') or None,
            "subject": metadata.get('subject') or None,
            "keywords": metadata.get('keywords') or None,
            "creator": metadata.get('creator') or None,
            "producer": metadata.get('producer') or None,
            "creation_date": creation_date,
            "modification_date": mod_date,
            "page_count": len(self.doc),
            "file_size_bytes": file_size,
            "file_size_formatted": self._format_file_size(file_size),
            "pdf_version": f"PDF {self.doc.metadata.get('format', 'Unknown')}",
        }
    
    def extract_text(
        self, 
        page_num: Optional[int] = None, 
        preserve_layout: bool = False
    ) -> str | Dict[int, str]:
        """
        Extract text from PDF
        
        Args:
            page_num: Specific page number (1-indexed). None for all pages.
            preserve_layout: If True, preserves layout with spacing and alignment.
                           If False, returns clean text with minimal formatting.
            
        Returns:
            If page_num specified: text string
            If page_num is None: dict mapping page numbers to text
        """
        if not self.doc:
            raise PDFReaderError("PDF not opened. Call open() first.")
        
        # Choose extraction mode
        # "text" = standard, clean text (good reading order)
        # "blocks" = preserves layout with spacing
        extract_mode = "blocks" if preserve_layout else "text"
        
        if page_num is not None:
            # Extract single page (1-indexed)
            if page_num < 1 or page_num > len(self.doc):
                raise PDFReaderError(
                    f"Invalid page number: {page_num}. Valid range: 1-{len(self.doc)}"
                )
            page = self.doc[page_num - 1]  # Convert to 0-indexed
            
            if preserve_layout:
                # Get blocks and sort by position (top to bottom, left to right)
                blocks = page.get_text("blocks")
                sorted_blocks = sorted(blocks, key=lambda b: (b[1], b[0]))
                text_parts = [b[4] for b in sorted_blocks if len(b) >= 5 and b[4].strip()]
                return "\n".join(text_parts)
            else:
                return page.get_text()
        
        # Extract all pages
        text_dict = {}
        for page_idx, page in enumerate(self.doc):
            if preserve_layout:
                blocks = page.get_text("blocks")
                sorted_blocks = sorted(blocks, key=lambda b: (b[1], b[0]))
                text_parts = [b[4] for b in sorted_blocks if len(b) >= 5 and b[4].strip()]
                text_dict[page_idx + 1] = "\n".join(text_parts)
            else:
                text_dict[page_idx + 1] = page.get_text()
        
        return text_dict
    
    def extract_text_with_layout(self, page_num: int) -> Dict[str, Any]:
        """
        Extract text with layout preserved (proper reading order)
        
        Uses PyMuPDF's "blocks" mode which maintains proper reading order
        with spacing and line breaks preserved.
        
        Args:
            page_num: Page number (1-indexed)
            
        Returns:
            Dictionary with text and layout information
        """
        if not self.doc:
            raise PDFReaderError("PDF not opened. Call open() first.")
        
        if page_num < 1 or page_num > len(self.doc):
            raise PDFReaderError(
                f"Invalid page number: {page_num}. Valid range: 1-{len(self.doc)}"
            )
        
        page = self.doc[page_num - 1]
        
        # Use "blocks" mode - preserves layout with proper spacing
        # PyMuPDF automatically sorts blocks in reading order (top to bottom, left to right)
        text = page.get_text("blocks")
        
        # Sort blocks by position (top to bottom, left to right)
        # Each block is: (x0, y0, x1, y1, "text", block_no, block_type)
        sorted_blocks = sorted(text, key=lambda b: (b[1], b[0]))  # Sort by y0, then x0
        
        formatted_blocks = []
        full_text_parts = []
        
        for block in sorted_blocks:
            # block structure: (x0, y0, x1, y1, text, block_no, block_type)
            if len(block) >= 7 and block[6] == 0:  # Text block (type 0)
                block_text = block[4].strip()
                if block_text:
                    formatted_blocks.append({
                        "bbox": [block[0], block[1], block[2], block[3]],
                        "text": block_text,
                    })
                    full_text_parts.append(block_text)
        
        # Join with single newline to preserve structure
        full_text = "\n".join(full_text_parts)
        
        return {
            "page_number": page_num,
            "text": full_text,
            "blocks": formatted_blocks,
            "block_count": len(formatted_blocks)
        }
    
    def get_page_dimensions(self, page_num: int) -> Dict[str, Any]:
        """
        Get page dimensions
        
        Args:
            page_num: Page number (1-indexed)
            
        Returns:
            Dictionary with width, height, and orientation
        """
        if not self.doc:
            raise PDFReaderError("PDF not opened. Call open() first.")
        
        if page_num < 1 or page_num > len(self.doc):
            raise PDFReaderError(
                f"Invalid page number: {page_num}. Valid range: 1-{len(self.doc)}"
            )
        
        page = self.doc[page_num - 1]
        rect = page.rect
        
        orientation = "portrait" if rect.height > rect.width else "landscape"
        if rect.height == rect.width:
            orientation = "square"
        
        return {
            "width": rect.width,
            "height": rect.height,
            "orientation": orientation
        }
    
    def extract_text_regions(self, page_num: int = 1) -> Dict[str, List[Dict]]:
        """
        Extract text blocks grouped by 6 regions
        Divides page into top and bottom halves, each split into left/center/right
        
        Args:
            page_num: Page number (1-indexed)
            
        Returns:
            Dictionary with region names as keys and list of text blocks as values
            Regions: top_left, top_center, top_right, bottom_left, bottom_center, bottom_right
        """
        if not self.doc:
            raise PDFReaderError("PDF not opened. Call open() first.")
        
        layout_data = self.extract_text_with_layout(page_num)
        dimensions = self.get_page_dimensions(page_num)
        
        width = dimensions["width"]
        height = dimensions["height"]
        
        # Define 6 regions (3 top + 3 bottom)
        regions = {
            "top_left": [],
            "top_center": [],
            "top_right": [],
            "bottom_left": [],
            "bottom_center": [],
            "bottom_right": []
        }
        
        for block in layout_data["blocks"]:
            bbox = block["bbox"]  # [x0, y0, x1, y1]
            x0, y0, x1, y1 = bbox
            
            # Calculate block center
            center_x = (x0 + x1) / 2
            center_y = (y0 + y1) / 2
            
            # Determine vertical position (top vs bottom)
            is_top = center_y < height * 0.5
            
            # Determine horizontal position (left/center/right)
            if center_x < width * 0.33:
                horizontal = "left"
            elif center_x < width * 0.67:
                horizontal = "center"
            else:
                horizontal = "right"
            
            # Assign to appropriate region
            region_key = f"{'top' if is_top else 'bottom'}_{horizontal}"
            regions[region_key].append(block)
        
        return regions
    
    def extract_images(self, page_num: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Extract image information from PDF
        
        Args:
            page_num: Specific page number (1-indexed). None for all pages.
            
        Returns:
            List of dictionaries containing image information
        """
        if not self.doc:
            raise PDFReaderError("PDF not opened. Call open() first.")
        
        images = []
        
        if page_num is not None:
            # Single page
            if page_num < 1 or page_num > len(self.doc):
                raise PDFReaderError(
                    f"Invalid page number: {page_num}. Valid range: 1-{len(self.doc)}"
                )
            pages_to_process = [page_num - 1]
        else:
            # All pages
            pages_to_process = range(len(self.doc))
        
        for page_idx in pages_to_process:
            page = self.doc[page_idx]
            image_list = page.get_images(full=True)
            
            for img_idx, img in enumerate(image_list):
                xref = img[0]
                images.append({
                    "page": page_idx + 1,  # 1-indexed
                    "image_index": img_idx,
                    "xref": xref,
                    "width": img[2],
                    "height": img[3],
                })
        
        return images
    
    def has_images(self) -> bool:
        """
        Check if PDF contains any images
        
        Returns:
            True if images found, False otherwise
        """
        images = self.extract_images()
        return len(images) > 0
    
    @staticmethod
    def _format_pdf_date(date_str: Optional[str]) -> Optional[str]:
        """
        Format PDF date string to ISO format
        
        Args:
            date_str: PDF date string (e.g., "D:20240101120000")
            
        Returns:
            ISO formatted date string or None
        """
        if not date_str:
            return None
        
        try:
            # PDF date format: D:YYYYMMDDHHmmSSOHH'mm
            if date_str.startswith("D:"):
                date_str = date_str[2:]
            
            # Take first 14 characters (YYYYMMDDHHmmSS)
            date_str = date_str[:14]
            
            # Parse and format
            dt = datetime.strptime(date_str, "%Y%m%d%H%M%S")
            return dt.isoformat()
        except Exception:
            return date_str  # Return original if parsing fails
    
    @staticmethod
    def _format_file_size(bytes_size: int) -> str:
        """
        Format bytes to human-readable string
        
        Args:
            bytes_size: Size in bytes
            
        Returns:
            Formatted string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"
    
    def extract_sender_recipient_blocks(self, page_num: int = 0) -> Dict[str, Any]:
        """
        Extract sender and recipient text blocks from PDF
        
        Strategy:
        1. Filter blocks before ETTN
        2. Filter left side (sender/recipient area)
        3. Split by "SAYIN" keyword
        
        Args:
            page_num: Page number (0-indexed)
            
        Returns:
            Dictionary with sender_blocks and recipient_blocks
        """
        import re
        
        if not self.doc:
            raise ValueError("PDF not loaded")
        
        page = self.doc[page_num]
        page_width = page.rect.width
        page_height = page.rect.height
        
        # Get all text blocks
        blocks = page.get_text("blocks")
        text_blocks = []
        for block in blocks:
            if block[6] == 0 and block[4].strip():  # text block
                text_blocks.append({
                    'x0': block[0],
                    'y0': block[1],
                    'x1': block[2],
                    'y1': block[3],
                    'text': block[4].strip(),
                    'width': block[2] - block[0],
                    'height': block[3] - block[1],
                    'center_x': (block[0] + block[2]) / 2,
                    'center_y': (block[1] + block[3]) / 2
                })
        
        # Sort by Y position
        sorted_blocks = sorted(text_blocks, key=lambda b: b['y0'])
        
        # === STEP 1: Filter before ETTN ===
        ettn_idx = None
        for i, block in enumerate(sorted_blocks):
            if 'ettn' in block['text'].lower():
                ettn_idx = i
                break
        
        before_ettn = sorted_blocks[:ettn_idx] if ettn_idx else sorted_blocks
        
        if not before_ettn:
            return {'sender_blocks': [], 'recipient_blocks': []}
        
        # === STEP 2: Filter left side ===
        sorted_by_x = sorted(before_ettn, key=lambda b: b['x0'])
        leftmost_x = sorted_by_x[0]['x0'] if sorted_by_x else 0
        x_threshold = leftmost_x + (page_width * 0.35)
        
        left_blocks = [b for b in before_ettn if b['x0'] < x_threshold]
        
        if not left_blocks:
            return {'sender_blocks': [], 'recipient_blocks': []}
        
        # === STEP 3: Minimal noise filtering (only obvious non-entity blocks) ===
        clean_blocks = []
        for block in left_blocks:
            text = block['text']
            text_lower = text.lower()
            
            # Filter only:
            # 1. Logo text (e-fatura, e-arşiv)
            # 2. Table headers (very distinctive keywords)
            # 3. Very short blocks (< 5 chars)
            
            # Logo
            if any(kw in text_lower for kw in ['e-fatura', 'e-arşiv']):
                continue
            
            # Table headers/content (only very specific patterns)
            if any(kw in text_lower for kw in [
                'sıra\nno', 'mal hizmet', 'malzeme/hizmet',
                'miktar', 'birim\nfiyat', 'kdv\noranı',
                'toplam\ntutar', 'iskonto\ntutarı'
            ]):
                continue
            
            # Too short (very aggressive threshold)
            if len(text.strip()) < 5:
                continue
            
            # Keep everything else (including Vergi No, Telefon, etc.)
            clean_blocks.append(block)
        
        if not clean_blocks:
            return {'sender_blocks': [], 'recipient_blocks': []}
        
        # === STEP 4: Split ONLY by "SAYIN" keyword ===
        # SAYIN is ALWAYS before recipient, and AFTER sender
        # This is the most reliable indicator in Turkish invoices
        
        sayin_idx = None
        sayin_pattern = re.compile(r'sa\s*y[iıİ]n', re.IGNORECASE)
        
        for i, block in enumerate(clean_blocks):
            if sayin_pattern.search(block['text'].lower()):
                sayin_idx = i
                break
        
        if sayin_idx is not None and sayin_idx > 0:
            # Split at SAYIN: everything before = sender, SAYIN and after = recipient
            sender_blocks = clean_blocks[:sayin_idx]
            recipient_blocks = clean_blocks[sayin_idx:]
        elif sayin_idx == 0:
            # SAYIN is first block (unlikely but handle it)
            sender_blocks = []
            recipient_blocks = clean_blocks
        else:
            # No SAYIN found - use biggest vertical gap as fallback
            if len(clean_blocks) >= 2:
                gaps = []
                for i in range(len(clean_blocks) - 1):
                    gap = clean_blocks[i + 1]['y0'] - clean_blocks[i]['y1']
                    if gap > 10:  # Minimum 10px gap
                        gaps.append({'index': i, 'gap': gap})
                
                if gaps:
                    best_gap = max(gaps, key=lambda g: g['gap'])
                    split_idx = best_gap['index']
                    sender_blocks = clean_blocks[:split_idx + 1]
                    recipient_blocks = clean_blocks[split_idx + 1:]
                else:
                    # No significant gap, assume first half is sender
                    mid = len(clean_blocks) // 2
                    sender_blocks = clean_blocks[:mid]
                    recipient_blocks = clean_blocks[mid:]
            else:
                sender_blocks = clean_blocks
                recipient_blocks = []
        
        # Ensure we have something
        if not sender_blocks and recipient_blocks:
            sender_blocks = [recipient_blocks[0]]
            recipient_blocks = recipient_blocks[1:]
        
        if not recipient_blocks and sender_blocks:
            recipient_blocks = [sender_blocks[-1]]
            sender_blocks = sender_blocks[:-1]
        
        return {
            'sender_blocks': sender_blocks,
            'recipient_blocks': recipient_blocks
        }
    
    def extract_invoice_metadata(self, page_num: int = 0) -> Dict[str, Any]:
        """
        Extract invoice metadata (right side key-value pairs)
        
        Typical fields:
        - Tarih / Date
        - Fatura No / Invoice No
        - Senaryo / Scenario
        - Sipariş No / Order No
        - Fatura Tipi / Invoice Type
        - Özelleştirme No
        - ETTN
        
        Returns:
            Dictionary with extracted metadata
        """
        import re
        
        if not self.doc:
            raise ValueError("PDF not loaded")
        
        page = self.doc[page_num]
        page_width = page.rect.width
        
        # Get all text blocks
        blocks = page.get_text("blocks")
        text_blocks = []
        for block in blocks:
            if block[6] == 0 and block[4].strip():  # text block
                text_blocks.append({
                    'x0': block[0],
                    'y0': block[1],
                    'text': block[4].strip()
                })
        
        # Filter right side (X > 40% of page width)
        right_blocks = [b for b in text_blocks if b['x0'] > page_width * 0.4]
        
        # Sort by Y position
        right_blocks.sort(key=lambda b: b['y0'])
        
        # Extract key-value pairs
        metadata = {}
        
        # Common invoice metadata keys (Turkish & English)
        key_patterns = {
            'tarih': ['tarih', 'date'],
            'fatura_no': ['fatura no', 'invoice no', 'invoice number', 'fatura numarası'],
            'senaryo': ['senaryo', 'scenario'],
            'siparis_no': ['sipariş no', 'siparis no', 'order no', 'order number'],
            'fatura_tipi': ['fatura tipi', 'invoice type', 'fatura türü'],
            'ozellestime_no': ['özelleştirme no', 'ozellestime no', 'customization no'],
            'ettn': ['ettn', 'e-fatura uuid'],
            'son_odeme_tarihi': ['son ödeme tarihi', 'son odeme tarihi', 'due date'],
            'olusma_zamani': ['oluşma zamanı', 'olusma zamani', 'creation time']
        }
        
        for block in right_blocks:
            text = block['text']
            text_lower = text.lower()
            
            # Check for key:value or key value patterns
            if ':' in text or '\n' in text:
                # Try to extract key-value
                lines = text.split('\n')
                for i in range(len(lines) - 1):
                    line = lines[i].strip()
                    value_line = lines[i + 1].strip() if i + 1 < len(lines) else ''
                    
                    # Match against known keys
                    for key, patterns in key_patterns.items():
                        for pattern in patterns:
                            if pattern in line.lower():
                                # Get value after ":"
                                if ':' in line:
                                    value = line.split(':', 1)[1].strip()
                                elif value_line:
                                    value = value_line
                                else:
                                    continue
                                
                                if value and key not in metadata:
                                    metadata[key] = value
                                    break
        
        return metadata

