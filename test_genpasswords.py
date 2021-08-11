from _pytest.tmpdir import TempdirFactory
import pytest
import genpasswords
import tempfile
import os

def test_invalid_wordfile():
  with pytest.raises(RuntimeError) as e:
    genpasswords.cli_main(('--words=README.md',))
  assert "No valid words found" in str(e)

def test_bad_kind():
  with pytest.raises(RuntimeError) as e:
    with tempfile.TemporaryDirectory() as tmp:
      badfile = os.path.join(tmp, 'badfile')
      with open(badfile, 'w') as f:
        f.write('foo=5:badkind\n')
      genpasswords.cli_main(('-i', badfile))
  assert "is not 'hex', 'words' or 'base64'" in str(e)

def test_missing_word_file():
  with pytest.raises(FileNotFoundError) as e:
    genpasswords.cli_main(
      ('--words', '/this/file/definately/does/not/exist')
    )
  assert "`--words` file not found" in str(e)

def test_words_file():
  with tempfile.TemporaryDirectory() as tmp:
    wordfile = os.path.join(tmp, "wordfile")
    with open(wordfile, 'w') as f:
      for i in range(10):
        f.write('bla' * i + '\n')
    genpasswords.cli_main(
      ('--words', wordfile)
    )
    with pytest.raises(RuntimeError) as e:
      genpasswords.cli_main((
        '--words', wordfile,
        '--bad-words', wordfile,
      ))
    assert "No valid words" in str(e)
