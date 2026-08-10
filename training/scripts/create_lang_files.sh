#!/bin/bash
# Crée les fichiers punc et numbers pour tesstrain
cd /home/hamoh/tmz_training/tesstrain/data/tmz_latn

# Fichier de ponctuation (un caractère par ligne)
cat > tmz_latn.punc << 'EOF'
.
,
;
:
!
?
-
(
)
«
»
"
'
…
–
—
[
]
/
EOF

# Fichier de chiffres
cat > tmz_latn.numbers << 'EOF'
0
1
2
3
4
5
6
7
8
9
EOF

echo "=== Fichiers créés ==="
echo "tmz_latn.punc :"
wc -l tmz_latn.punc
echo "tmz_latn.numbers :"
wc -l tmz_latn.numbers
echo "tmz_latn.wordlist :"
wc -l tmz_latn.wordlist
echo "=== OK ==="
