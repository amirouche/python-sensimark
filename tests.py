from wikimark import html2paragraph


class TestHTML2Paragraph:

    def test_base(self):
        with open('data/test/base.html') as f:
            input = f.read()
        out = html2paragraph(input)
        with open('data/test/base.txt') as f:
            expected = f.read()
        assert out.stringify() == expected
