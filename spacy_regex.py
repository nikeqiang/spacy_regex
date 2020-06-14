"""
Extension to easily search spacy doc / spacy spans
using standard regex functions finditer / findall
(with decent effeciency and without worrying
about whitespace or intra-token matches)
[Can be further extented to support additional regex integration]

usage:  doc._.finditer(regex_pattern, flags)
        doc._.findall(regex_pattern, flags)
        span._.finditer(regex_pattern, flags)
        span._.findall(regex_pattern, flags)

>>> text = '''Work done with anxiety about results is far
>>> inferior to work done without such anxiety, in the calm of
>>> self surrender. - Baghavad Gita (400 BCE - 200 CE) '''
>>> doc = nlp(text)
>>> doc._.findall('B\w+|\w+\,', flags=re.I)
>>> # Out[1]: [about, anxiety,, Baghavad, BCE]
>>> doc._.finditer('B\w+|\w+\,')
>>> # Out[2]: <generator object doc_finditer at 0x11b7a1b48>
>>> [(s.start, s.end, s.text) for s in doc._.finditer('B\w+|\w+\,')]
>>> # Out[3]: [(15, 17, 'anxiety,'), (26, 27, 'Baghavad'), (30, 31, 'BCE')]
>>> doc[2:5]._.findall('a[\w ]+')
>>> # Out[4]: [anxiety about]
"""
from spacy.tokens.doc import Doc
from spacy.tokens.span import Span
from typing import *
import re


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# idx2ti
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
def _chr2tok(spacy_doc: Doc) -> Dict[int, int]:
    """mapping of char offset to token index; token whitespace included; faster than approch in documentation"""
    d = {tok.idx: i for i, tok in enumerate(spacy_doc)}
    i = 0
    for idx in range(spacy_doc[-1].idx + len(spacy_doc[-1].text) + 1):
        if idx in d:
            i = d[idx]
        else:
            d[idx] = i
    return d


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Doc extensions to set mapping of chr offsets ("idx") to token index ("ti")
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

Doc.set_extension('_idx_to_ti_map', default=None)


def set_idx_to_ti_map(doc):
    doc._._idx_to_ti_map = _chr2tok(doc)


def get_idx_to_ti_map(doc):
    if doc._._idx_to_ti_map is None:
        set_idx_to_ti_map(doc)
    return doc._._idx_to_ti_map


Doc.set_extension('idx_to_ti_map', getter=get_idx_to_ti_map)


def get_ti_from_idx(doc, idx):
    return doc._.idx_to_ti_map[idx]


Doc.set_extension('idx2ti', method=get_ti_from_idx)


def get_tok_from_idx(doc, idx):
    return doc[doc._.idx_to_ti_map[idx]]


Doc.set_extension('idx2tok', method=get_tok_from_idx)


def get_span_from_idxs(doc: Doc, idx_start: int, idx_end: int):
    """Needs testing
    test: ensure that doc.text[idx_start:idx_end] in doc[start_i:end_i+1].text for all
    """
    start_i = doc._.idx2ti(idx_start)
    
    if idx_start == idx_end:
        return doc[start_i:start_i]
    
    end_i = doc._.idx2ti(idx_end - 1)  # - 1 as text[idx_start:idx_end] doesn't include idx_end char
    return doc[start_i:end_i + 1]


Doc.set_extension('idxs2span', method=get_span_from_idxs)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Doc extensions for standard regex functions 'finditer' and 'findall'
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def doc_finditer(doc: Doc, pattern: str, flags=0) -> Iterator[Span]:
    for m in re.finditer(pattern=pattern, string=doc.text, flags=flags):
        yield doc._.idxs2span(*m.span())


Doc.set_extension('finditer', method=doc_finditer)


def doc_findall(doc: Doc, pattern, flags=0) -> List[Span]:
    return list(doc._.finditer(pattern, flags=flags))


Doc.set_extension('findall', method=doc_findall)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Span extensions for standard regex functions 'finditer' and 'findall'
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def span_finditer(span: Span, pattern, flags=0):
    span_start_idx = span[0].idx
    for m in re.finditer(pattern=pattern, string=span.text, flags=flags):
        start, end = m.span()
        start += span_start_idx
        end += span_start_idx
        yield span.doc._.idxs2span(start, end)


Span.set_extension('finditer', method=span_finditer)


def span_findall(span, pattern, flags=0):
    return list(span._.finditer(pattern, flags=flags))


Span.set_extension('findall', method=span_findall)

