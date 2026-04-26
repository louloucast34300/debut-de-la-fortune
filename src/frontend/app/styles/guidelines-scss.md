# Guidelines SCSS — Début de la Fortune

## 1. Structure

```
styles/
  config/
    _variables.scss       ← couleurs de marque, breakpoints, tailles de layout
    _mixins.scss          ← patterns CSS réutilisables et non triviaux
    _typography.scss      ← @import Google Fonts (une seule fois ici)
  features/               ← miroir de app/features/ (1er niveau seulement)
  components/             ← miroir de app/components/
  commons/                ← patterns de composants partagés entre features
  index.scss              ← @forward de tous les partiels
```

---

## 1.2 Dossier `features/`

Les fichiers suivent la même arborescence que `app/features/`, en s'arrêtant au **premier niveau de dossier**.

```
app/features/auth/login              → styles/features/auth/_login.scss
app/features/auth/register           → styles/features/auth/_register.scss
app/features/auth/login/atomic/logout → styles/features/auth/_logout.scss
```

---

## 1.3 Dossier `components/`

Les fichiers suivent la même arborescence que `app/components/`.

```
app/components/navigation → styles/components/_navigation.scss
```

---

## 1.4 Dossier `commons/`

Contient tout ce qui est réutilisable entre plusieurs features ou composants.

- Si c'est un **bloc de CSS avec imbrication** → fichier dans `commons/`
- Si c'est un **pattern CSS réutilisable et non trivial** → mixin dans `_mixins.scss`

```scss
// commons/ — exemple de bloc partagé
.image-section {
    position: relative;
    overflow: hidden;
    img { object-fit: cover; }
}

// _mixins.scss — exemple de pattern non trivial
@mixin btn-kitsch { ... } // hover + active + ombre 3D → justifie une mixin
```

---

## 2. Variables et mixins — quoi abstraire

### Variables (`_variables.scss`)

Variabiliser uniquement ce qui a une **signification sémantique** ou qui est susceptible de **changer globalement**.

✅ À variabiliser :
- Couleurs de marque (`$gold`, `$cyan`, `$pink`) — si on rebrande, on change à un seul endroit
- Breakpoints (`$breakpoint-mobile`) — doit rester cohérent sur tout le projet
- Tailles de layout structurel (`$auth-panel-width`)

❌ À ne pas variabiliser :
- Valeurs cosmétiques locales (`border-radius: 16px` dans une card spécifique)
- Valeurs évidentes et non partagées (`padding: 40px`)

### Mixins (`_mixins.scss`)

Créer une mixin uniquement si le bloc est **sémantiquement identifiable** et **non trivial**.

✅ Bonne mixin :
```scss
@mixin btn-kitsch { ... } // pattern complet avec états hover/active/shadow
```

❌ Mauvaise mixin :
```scss
@mixin flex-center {       // 3 lignes lisibles directement, la mixin est plus obscure
    display: flex;
    align-items: center;
    justify-content: center;
}
```

> **Règle heuristique** : si en lisant le SCSS, un dev doit aller chercher la définition pour comprendre ce que ça fait, c'est probablement trop abstrait.

---

## 3. Conventions de nommage

- Classes en **kebab-case** uniquement (pas de camelCase, pas de PascalCase)
- Les partiels SCSS commencent toujours par `_` (ex: `_login.scss`)
- Les fichiers dans `config/` ne génèrent **aucun CSS** (variables, mixins et fonctions uniquement)

---

## 4. Règles d'import

- Toujours `@use '../config/variables' as *` — jamais `@import`
- Jamais de `@import url(...)` en dehors de `_typography.scss`
- Jamais de `@forward` en dehors de `index.scss`

---

## 5. Checklist avant de générer du nouveau SCSS

---

## 6. Direction artistique (DA)

Le site a un univers visuel **kitsch game-show télévisé** inspiré de Wheel of Fortune. Tout nouveau composant ou feature doit s'inscrire dans cette DA.

### Palette
| Rôle | Variable | Valeur |
|---|---|---|
| Fond sombre | `$purple-dark` / `$purple-deep` | `#3b0070` / `#1a003a` |
| Accent principal | `$gold` | `#e7b100` |
| Accent secondaire | `$cyan` | `#00e5ff` |
| Accent tertiaire | `$pink` | `#ff3cac` |

### Typographie
- Police principale : **Fredoka One** (`$font-kitsch`) — titres, boutons, labels
- Effets néon sur les textes importants (`text-shadow` avec la couleur du texte)
- Lettres en majuscules avec `letter-spacing` sur les titres et CTA

### Composants de référence
La **page login/register** est la référence DA du projet :
- Fonds : dégradé `$purple-dark → $purple-deep`
- Bordures : `3-6px solid $gold`
- Ombres : `box-shadow` ambré + glow intérieur violet
- Boutons CTA : dégradé or avec ombre 3D (`@include btn-kitsch`)
- Boutons secondaires : contour néon (`@include btn-outline($color)`)
- Séparateurs : dégradé arc-en-ciel (`@include rainbow-divider`)

> **Tout composant qui s'écarte de cette DA (fonds neutres `#1a1a2e`, bordures grises, boutons sans néon) doit être corrigé pour s'y conformer.**

1. Parcourir `styles/` pour vérifier qu'aucun style similaire n'existe déjà
2. Les couleurs et tailles structurelles utilisent les variables existantes (pas de valeurs hardcodées si `$gold` existe)
3. Le nouveau fichier est référencé dans `index.scss`
4. Pas de styles inline `style={{}}` dans les `.tsx` pour du styling structurel

