Ce code propose une application python permettant la création d'un Dashboard des dépenses d'un compte courant stocké au format csv et structuré de la manière suivante :
  - Colonne obligatoire : Date opération ; Libellé opération ; Catégorie ; Sous-catégorie ; Montant
  - Type : Date ; string ; string ; string ; float
  - La colonne Catégorie est composé de 3 modalités (Dépense, Revenus, Epargne) : seul Epargne est obligatoire, Dépense et Revenus sont déterminés selon le signe du montant.
  - La colonne Sous-catégorie
Si vous ne disposez pas de données au bon format, un excel comportant des dépenses générées aléatoirement a été déposé dans le répertoire. 

Environnement : Python 3.11.1
  1. pip install 'requirements.txt'
  2. Lancer le pichier 'app.py'
  3. Une page internet s'ouvre sur votre navigateur par défaut, dans celle-ci le dashboard vide de données.
  4. Uploader vos données dans l'encadré prévu à cet effet (Drag&Drop ou click)
