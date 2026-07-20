"""Shared wrapper layer over the ragleakguard package (PyPI, version-pinned).

Both agencies in this repo (AI Data Security Auditor, Safe RAG Agent) route
every scan through this layer, which reduces raw detector findings to
findings-METADATA before anything reaches the model or the chat transcript.
"""
