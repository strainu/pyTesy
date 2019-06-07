rm dist/*
python3 setup.py sdist bdist_wheel
python3 -m twine upload -u styrahem -p i42YFZ7YjZFcp6t dist/*

