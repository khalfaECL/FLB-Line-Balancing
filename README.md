
# 🧵 Équilibrage de Ligne de Production Textile

Ce projet met en œuvre un **modèle mathématique personnalisé** pour équilibrer des lignes de production dans l'industrie textile. Il repose sur l’analyse automatique de gammes opératoires et une allocation optimale des tâches dans le respect des contraintes industrielles (Takt Time, nombre d'opérateurs, etc.).

---

## 📌 Objectifs

- Extraire et structurer les opérations issues de gammes de fabrication.
- Répartir les tâches sur plusieurs postes en optimisant l'équilibrage.
- Évaluer la performance à l’aide d’indicateurs : efficience, fluidité, équilibre des charges.
- Visualiser les affectations sous forme de diagrammes Yamazumi.

---

## 🧠 Modèle mathématique

Le cœur du projet est un algorithme d’optimisation sur-mesure, respectant :
- Les contraintes de précédence définies selon une logique métier.
- Une borne supérieure (Takt Time) par poste.
- La minimisation du déséquilibre entre postes.

Aucune heuristique classique (type SPT, RPW) n'est utilisée ici.

---

## 📊 Indicateurs Clés

- **Efficience (%)** = Temps utile / Temps alloué total
- **Indice de fluidité** = Écart-type des charges poste / Takt Time
- **Nombre de postes utilisés** = Allocation en fonction du Takt Time et de la durée totale

---

## 🔍 Exemple d'utilisation

```bash
# Lancer le notebook
jupyter notebook MTE1.ipynb
```

- Lire automatiquement les opérations depuis le fichier Excel
- Lancer l'algorithme d'équilibrage
- Visualiser les tâches affectées à chaque poste + histogramme Yamazumi

---

## 📦 Technologies

- Python 3.x
- Pandas, NumPy
- Matplotlib
- Jupyter Notebook

---

## ✍️ Auteurs

Projet réalisé dans le cadre d’un cas réel d’optimisation industrielle dans l’industrie de la confection textile.  
Encadré par des experts métier et basé sur des données issues d’ateliers marocains.
