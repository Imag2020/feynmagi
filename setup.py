###########################################################################################
#
# FeynmAGI V0.1.1
# Imed MAGROUNE
# 2024-06
#
#########################################################################################
from setuptools import setup, find_packages

# Fonction pour lire le fichier requirements.txt
def parse_requirements(filename):
    with open(filename, 'r', encoding='utf-8' ) as file:
        lines = file.readlines()
    # Retirer les commentaires et les lignes vides
    lines = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
    return lines

setup(
    name='feynmagi',
    version='0.1.24',
    packages=find_packages(),
    include_package_data=True,
    install_requires=parse_requirements('requirements.txt'),
    entry_points={
        'console_scripts': [
            'feynmagi=feynmagi.feynmagi:main',
        ],
    },
    author='Imed MAGROUNE',
    author_email='imed@magroune.net',
    description='Feynmagi is a multi-modal LLM interactive agents solution.',
    long_description=open('README.md',encoding='utf-8' ).read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Imag2020/feynmagi',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',    
)

