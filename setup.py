from setuptools import setup, find_packages

setup(
    name='bicimad',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'requests==2.32.3',
        'numpy==2.1.2',
        'pandas==2.2.3',
        'matplotlib==3.9.2',        
    ],
    include_package_data=True,  # Incluye archivos de datos especificados en MANIFEST.in
    description='Paquete para gestionar y analizar datos de uso de bicicletas de la EMT de Madrid.',
    long_description=open('README.md').read(),  # Lee el contenido de README.md como descripción larga
    long_description_content_type='text/markdown',  # Especifica que la descripción está en formato Markdown
    author='Víctor Daniel Rodríguez',  # Reemplaza con tu nombre
    author_email='victor.rdrgz.prz@gmail.com',  # Reemplaza con tu correo electrónico
    url='https://github.com/tuusuario/bicimad',  # Reemplaza con la URL de tu proyecto
    license='MIT',  # Tipo de licencia
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',  # Versión mínima de Python requerida
)