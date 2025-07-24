import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from app.storage.embeddings import EmbeddingGenerator
from tenacity import RetryError


@pytest.mark.unit
@pytest.mark.parametrize(
    "text,expected_input",
    [
        ("hello", "hello"),
        ("x" * 8500, "x" * 8000),
    ],
)
def test_generate_embedding_truncation(text, expected_input, mock_settings):
    """Embedding generation should truncate long texts and call OpenAI once."""
    response = MagicMock()
    response.data = [MagicMock(embedding=[0.5, 0.5])]
    client = MagicMock()
    client.embeddings.create.return_value = response
    with patch("app.storage.embeddings.OpenAI", return_value=client) as mock_cls:
        gen = EmbeddingGenerator()
        result = gen.generate_embedding(text)

    assert np.allclose(result, np.array([0.5, 0.5]))
    mock_cls.assert_called_once_with(api_key=mock_settings.openai_api_key)
    client.embeddings.create.assert_called_once_with(
        model="text-embedding-ada-002", input=expected_input
    )


@pytest.mark.unit
def test_generate_embedding_empty_text():
    gen = EmbeddingGenerator()
    with pytest.raises(RetryError):
        gen.generate_embedding(" ")


@pytest.mark.unit
def test_generate_embedding_invalid_provider():
    gen = EmbeddingGenerator(provider="other")
    result = gen.generate_embedding("text")
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize("batch_size,expected_calls", [(2, 1), (1, 2)])
async def test_generate_embeddings_batch(batch_size, expected_calls):
    gen = EmbeddingGenerator()
    with patch.object(gen, "_process_batch", return_value=[np.array([1])]) as mb:
        results = await gen.generate_embeddings_batch(["a", "b"], batch_size=batch_size)
    assert len(results) == 1 * expected_calls
    assert mb.call_count == expected_calls


@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_batch_handles_errors():
    gen = EmbeddingGenerator()
    seq = [np.array([1]), Exception("fail"), np.array([2])]

    def side_effect(_):
        value = seq.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

    with patch.object(gen, "generate_embedding", side_effect=side_effect):
        results = await gen._process_batch(["a", "b", "c"])

    assert len(results) == 3
    assert np.array_equal(results[0], np.array([1]))
    assert np.array_equal(results[1], np.zeros(1536))
    assert np.array_equal(results[2], np.array([2]))


@pytest.mark.unit
def test_embed_data_record_calls_generate_embedding(monkeypatch):
    record = {"title": "T", "views": 1, "tags": ["a", "b"]}
    with patch.object(EmbeddingGenerator, "generate_embedding", return_value=np.array([1])) as mock_gen:
        gen = EmbeddingGenerator()
        result = gen.embed_data_record(record)
    assert np.array_equal(result, np.array([1]))
    arg = mock_gen.call_args[0][0]
    assert "title: T" in arg
    assert "views: 1" in arg
    assert "tags: a, b" in arg


@pytest.mark.unit
def test_embed_data_record_no_text():
    gen = EmbeddingGenerator()
    with pytest.raises(ValueError, match="No textual content found"):
        gen.embed_data_record({})


@pytest.mark.unit
def test_embed_page_content_truncates_and_calls_generate(monkeypatch):
    content = "a" * 4500
    with patch.object(EmbeddingGenerator, "generate_embedding", return_value=np.array([2])) as mock_gen:
        gen = EmbeddingGenerator()
        result = gen.embed_page_content("Title", content, {"author": "A"})
    assert np.array_equal(result, np.array([2]))
    call_text = mock_gen.call_args[0][0]
    assert "Title: Title" in call_text
    assert "author: A" in call_text
    assert "Content: " in call_text
    assert content[:2000] in call_text and content[-2000:] in call_text


@pytest.mark.unit
def test_embed_page_content_no_content():
    gen = EmbeddingGenerator()
    with pytest.raises(ValueError, match="No content available"):
        gen.embed_page_content("", "", None)


@pytest.mark.unit
def test_calculate_similarity():
    gen = EmbeddingGenerator()
    v1 = np.array([1.0, 1.0])
    v2 = np.array([1.0, 1.0])
    v3 = np.array([1.0, 0.0])
    v4 = np.array([0.0, 1.0])
    assert gen.calculate_similarity(v1, v2) == pytest.approx(1.0)
    assert gen.calculate_similarity(v3, v4) == pytest.approx(0.0)
    assert gen.calculate_similarity(np.zeros(2), v1) == 0.0


@pytest.mark.unit
def test_get_embedding_dimension():
    assert EmbeddingGenerator(model="text-embedding-ada-002").get_embedding_dimension() == 1536
    assert EmbeddingGenerator(model="text-embedding-3-large").get_embedding_dimension() == 3072
    assert EmbeddingGenerator(model="unknown-model").get_embedding_dimension() == 1536
