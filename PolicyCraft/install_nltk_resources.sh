#!/bin/bash
set -e

# Bazowy katalog dla NLTK na macOS/Linux
NLTK_DIR="$HOME/nltk_data"
CORPORA_DIR="$NLTK_DIR/corpora"
TAGGERS_DIR="$NLTK_DIR/taggers"
TOKENIZERS_DIR="$NLTK_DIR/tokenizers"

echo "Tworzę katalogi..."
mkdir -p "$CORPORA_DIR" "$TAGGERS_DIR" "$TOKENIZERS_DIR"

# URLs paczek NLTK
WORDNET_URL="https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/wordnet.zip"
STOPWORDS_URL="https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/stopwords.zip"
TAGGER_URL="https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/taggers/averaged_perceptron_tagger.zip"
PUNKT_URL="https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/tokenizers/punkt.zip"

# Pobierz paczki
echo "Pobieram WordNet..."
curl -L -o /tmp/wordnet.zip "$WORDNET_URL"

echo "Pobieram Stopwords..."
curl -L -o /tmp/stopwords.zip "$STOPWORDS_URL"

echo "Pobieram averaged_perceptron_tagger..."
curl -L -o /tmp/averaged_perceptron_tagger.zip "$TAGGER_URL"

echo "Pobieram Punkt..."
curl -L -o /tmp/punkt.zip "$PUNKT_URL"

# Wypakuj
echo "Rozpakowuję WordNet..."
unzip -o /tmp/wordnet.zip -d "$CORPORA_DIR"

echo "Rozpakowuję Stopwords..."
unzip -o /tmp/stopwords.zip -d "$CORPORA_DIR"

echo "Rozpakowuję averaged_perceptron_tagger..."
unzip -o /tmp/averaged_perceptron_tagger.zip -d "$TAGGERS_DIR"

echo "Rozpakowuję Punkt..."
unzip -o /tmp/punkt.zip -d "$TOKENIZERS_DIR"

echo "✓ Gotowe! Zasoby NLTK są w $NLTK_DIR"
echo "Jeśli aplikacja ich nie widzi, ustaw zmienną środowiskową:"
echo "   export NLTK_DATA=\"$NLTK_DIR\""

