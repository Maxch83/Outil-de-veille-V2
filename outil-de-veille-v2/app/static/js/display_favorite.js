document.addEventListener('DOMContentLoaded', (event) => {
    const buttons = document.querySelectorAll('.btn-group .btn');
    const selectedFavorites = new Set();

    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const favoriteId = this.getAttribute('data-favorite-id');

            if (this.classList.contains('active')) {
                this.classList.remove('active');
                selectedFavorites.delete(favoriteId);
            } else {
                this.classList.add('active');
                selectedFavorites.add(favoriteId);
            }

            fetchArticlesByFavorites(Array.from(selectedFavorites));
        });
    });

    const exportButton = document.getElementById('export-button');
    const removeAllFavoritesButton = document.getElementById('remove-all-favorites');

    // Fonction pour vérifier s'il y a des articles avec des favoris
    function checkFavorites() {
        const articlesWithFavorites = document.querySelectorAll('.select-selected i.fa-solid.fa-bookmark');
        if (articlesWithFavorites.length > 0) {
            exportButton.disabled = false; // Activer le bouton
        } else {
            exportButton.disabled = true; // Désactiver le bouton
        }
    }

    // Vérifiez les favoris au chargement de la page
    checkFavorites();

    // Si les favoris sont modifiés, vérifier à nouveau
    document.querySelectorAll('.favorite-item').forEach(item => {
        item.addEventListener('click', function() {
            checkFavorites(); // Vérifiez les favoris après chaque modification
        });
    });

    // Vérifiez les favoris après suppression de tous les favoris
    removeAllFavoritesButton.addEventListener('click', function() {
        setTimeout(() => {
            checkFavorites(); // Vérifiez les favoris après une petite attente pour laisser le temps au DOM de se mettre à jour
        }, 100); // Temps d'attente pour que la suppression soit bien effectuée
    });

    // Si un favori est retiré, désactiver le bouton
    document.addEventListener('change', function() {
        checkFavorites();
    });

    document.getElementById('export-button').addEventListener('click', function() {
        window.location.href = '/export_articles';
    });

    document.getElementById('clear-favorites').addEventListener('click', function() {
        selectedFavorites.clear();
        buttons.forEach(button => button.classList.remove('active'));
        fetchArticlesByFavorites([]); // Pass an empty array to fetch all articles
    });

    // Fetch all articles at page load by passing all favorite IDs
    const allFavoriteIds = Array.from(buttons).map(button => button.getAttribute('data-favorite-id'));
    fetchArticlesByFavorites(allFavoriteIds);
});

function fetchArticlesByFavorites(favoriteIds) {
    fetch(`/articles_by_favorites`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ favorite_ids: favoriteIds })
    })
    .then(response => response.json())
    .then(data => {
        const articlesContainer = document.getElementById('articles-container');
        articlesContainer.innerHTML = ''; // Clear existing articles
        if (data.articles.length === 0) {
            const noArticlesMessage = document.createElement('div');
            noArticlesMessage.classList.add('text-center', 'mt-4');
            noArticlesMessage.innerText = 'Aucun article n\'a été ajouté dans les catégories sélectionnées.';
            articlesContainer.appendChild(noArticlesMessage);
        } else {
            data.articles.forEach(article => {
                const articleElement = document.createElement('div');
                articleElement.classList.add('list-group-item', 'm-0', 'p-1');
                articleElement.innerHTML = `
                    <div class="row" style="width: 103%;">
                        <p class="col-2">${article.published}</p>
                        <a class="col-6 nocolor" href="${article.link}" target="_blank">${article.title}</a>
                        <p class="col-2">${article.website_title}</p>
                        <div class="col-2 d-flex justify-content-end">
                            <button type="button" id="clear-favorites" class="btn btn-sm icon-container remove-favorite" data-article-id="${article.id}">
                                <div class="fa-solid fa-trash icon"></div>
                            </button>
                        </div>
                    </div>
                    <span class="badge" style="background-color: ${article.favorite_color}; color: ${calculateTextColor(article.favorite_color)};">${article.favorite_name}</span>
                `;
                articlesContainer.appendChild(articleElement);
            });
            
            applyTheme(localStorage.getItem('theme') || 'light');

            // Attacher des événements aux boutons de suppression de favori
            document.querySelectorAll('.remove-favorite').forEach(button => {
                button.addEventListener('click', function() {
                    const articleId = this.getAttribute('data-article-id');
                    updateFavorite(articleId, null);

                    // Mettre à null a l'affichage les formulaires de favoris
                    const form = document.getElementById(`dropdownForm-${articleId}`);
                    if (form) {
                        const favoriteItem = form.querySelector('.select-items div[data-value="None"]');
                        if (favoriteItem) {
                            form.querySelector('.select-selected').innerHTML = favoriteItem.innerHTML;
                            form.querySelector('input[name="selectedItem"]').value = null;
                        }
                    } else {
                        console.error('Form with ID not found:', formId);
                    }
                });
            });
        }
    });
}

function updateFavorite(articleId, favoriteId) {
    fetch('/update_article_favorite', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            favorite_id: favoriteId, 
            article_id: articleId 
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Mettre à jour l'affichage de l'élément sélectionné
            fetchArticlesByFavorites([]); // Met à jour l'affichage
        } else {
            alert('Failed to update favorite');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}