#!/usr/bin/env python
# This script will create the admin templates that extend the base.html file

# Users template
users_html = '''{% extends 'admin/base.html' %}
{% load static %}

{% block title %}Gestion des Utilisateurs | Administration{% endblock %}

{% block content %}
<div class="container-fluid">
  <div class="d-flex justify-content-between align-items-center mb-4">
    <h1 class="h2">Gestion des Utilisateurs</h1>
    <button class="btn btn-primary">
      <i class="bi bi-person-plus-fill"></i> Ajouter un utilisateur
    </button>
  </div>

  <!-- Statistics Row -->
  <div class="row mb-4">
    <div class="col-md-3">
      <div class="stats-card">
        <div class="icon text-primary">
          <i class="bi bi-people-fill"></i>
        </div>
        <div class="count">{{ stats.total }}</div>
        <div class="title">Total Utilisateurs</div>
      </div>
    </div>
    
    <div class="col-md-3">
      <div class="stats-card">
        <div class="icon text-warning">
          <i class="bi bi-person"></i>
        </div>
        <div class="count">{{ stats.clients }}</div>
        <div class="title">Clients</div>
      </div>
    </div>
    
    <div class="col-md-3">
      <div class="stats-card">
        <div class="icon text-success">
          <i class="bi bi-person-badge"></i>
        </div>
        <div class="count">{{ stats.experts }}</div>
        <div class="title">Experts</div>
      </div>
    </div>
    
    <div class="col-md-3">
      <div class="stats-card">
        <div class="icon text-info">
          <i class="bi bi-person-check"></i>
        </div>
        <div class="count">{{ stats.active }}</div>
        <div class="title">Utilisateurs Actifs</div>
      </div>
    </div>
  </div>

  <!-- Users List -->
  <div class="card">
    <div class="card-header bg-white">
      <h5 class="card-title mb-0">Liste des Utilisateurs</h5>
    </div>
    <div class="card-body">
      <div class="table-responsive">
        <table class="table table-hover">
          <thead>
            <tr>
              <th>Nom</th>
              <th>Email</th>
              <th>Type</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {% for user in users %}
            <tr>
              <td>{{ user.first_name }} {{ user.name }}</td>
              <td>{{ user.email }}</td>
              <td>{{ user.account_type|title }}</td>
              <td>
                {% if user.is_active %}
                <span class="badge bg-success">Actif</span>
                {% else %}
                <span class="badge bg-danger">Inactif</span>
                {% endif %}
              </td>
              <td>
                <div class="btn-group">
                  <button class="btn btn-sm btn-outline-primary">
                    <i class="bi bi-eye"></i>
                  </button>
                  <button class="btn btn-sm btn-outline-secondary">
                    <i class="bi bi-pencil"></i>
                  </button>
                </div>
              </td>
            </tr>
            {% empty %}
            <tr>
              <td colspan="5" class="text-center">Aucun utilisateur trouvé</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>
{% endblock %}'''

# Documents template
documents_html = '''{% extends 'admin/base.html' %}
{% load static %}

{% block title %}Gestion des Documents | Administration{% endblock %}

{% block content %}
<div class="container-fluid">
  <div class="d-flex justify-content-between align-items-center mb-4">
    <h1 class="h2">Gestion des Documents</h1>
  </div>

  <!-- Statistics Row -->
  <div class="row mb-4">
    <div class="col-md-3">
      <div class="stats-card">
        <div class="icon text-primary">
          <i class="bi bi-file-earmark"></i>
        </div>
        <div class="count">{{ stats.total }}</div>
        <div class="title">Total Documents</div>
      </div>
    </div>
    
    <div class="col-md-3">
      <div class="stats-card">
        <div class="icon text-success">
          <i class="bi bi-file-earmark-check"></i>
        </div>
        <div class="count">{{ stats.verified }}</div>
        <div class="title">Documents Vérifiés</div>
      </div>
    </div>
    
    <div class="col-md-3">
      <div class="stats-card">
        <div class="icon text-warning">
          <i class="bi bi-file-earmark-break"></i>
        </div>
        <div class="count">{{ stats.pending }}</div>
        <div class="title">En Attente</div>
      </div>
    </div>
    
    <div class="col-md-3">
      <div class="stats-card">
        <div class="icon text-danger">
          <i class="bi bi-file-earmark-x"></i>
        </div>
        <div class="count">{{ stats.rejected }}</div>
        <div class="title">Refusés</div>
      </div>
    </div>
  </div>

  <!-- Filter Section -->
  <div class="filter-section mb-4">
    <form method="get" class="row g-3">
      <div class="col-md-3">
        <label for="client" class="form-label">Client</label>
        <select id="client" name="client" class="form-select">
          <option value="">Tous les clients</option>
          {% for client in clients %}
          <option value="{{ client.id }}" {% if client_id|stringformat:"s" == client.id|stringformat:"s" %}selected{% endif %}>
            {{ client.user.first_name }} {{ client.user.name }}
          </option>
          {% endfor %}
        </select>
      </div>
      
      <div class="col-md-3">
        <label for="document-type" class="form-label">Type de document</label>
        <select id="document-type" name="type" class="form-select">
          <option value="">Tous les types</option>
          {% for type in document_types %}
          <option value="{{ type }}" {% if document_type == type %}selected{% endif %}>{{ type }}</option>
          {% endfor %}
        </select>
      </div>
      
      <div class="col-md-2">
        <label for="status" class="form-label">Statut</label>
        <select id="status" name="status" class="form-select">
          <option value="">Tous</option>
          <option value="pending" {% if status_filter == 'pending' %}selected{% endif %}>En attente</option>
          <option value="verified" {% if status_filter == 'verified' %}selected{% endif %}>Vérifié</option>
          <option value="rejected" {% if status_filter == 'rejected' %}selected{% endif %}>Refusé</option>
        </select>
      </div>
      
      <div class="col-md-2">
        <label for="search" class="form-label">Recherche</label>
        <input type="text" class="form-control" id="search" name="search" value="{{ search_query }}">
      </div>
      
      <div class="col-md-2 d-flex align-items-end">
        <button type="submit" class="btn btn-primary w-100">
          <i class="bi bi-filter"></i> Filtrer
        </button>
      </div>
    </form>
  </div>

  <!-- Documents List -->
  <div class="card">
    <div class="card-header bg-white">
      <h5 class="card-title mb-0">Liste des Documents</h5>
    </div>
    <div class="card-body">
      <div class="table-responsive">
        <table class="table table-hover">
          <thead>
            <tr>
              <th>Nom du document</th>
              <th>Client</th>
              <th>Demande</th>
              <th>Type</th>
              <th>Date d'ajout</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {% for doc in documents %}
            <tr>
              <td>{{ doc.name }}</td>
              <td>{{ doc.request.client.user.first_name }} {{ doc.request.client.user.name }}</td>
              <td>{{ doc.request.service.name }}</td>
              <td>{{ doc.document_type }}</td>
              <td>{{ doc.uploaded_at|date:"d/m/Y H:i" }}</td>
              <td>
                {% if doc.status == 'verified' %}
                <span class="badge bg-success">Vérifié</span>
                {% elif doc.status == 'rejected' %}
                <span class="badge bg-danger">Refusé</span>
                {% else %}
                <span class="badge bg-warning">En attente</span>
                {% endif %}
              </td>
              <td>
                <div class="btn-group">
                  <a href="{{ doc.file.url }}" target="_blank" class="btn btn-sm btn-outline-primary">
                    <i class="bi bi-eye"></i>
                  </a>
                  <button class="btn btn-sm btn-outline-success" data-bs-toggle="modal" data-bs-target="#verifyModal{{ doc.id }}">
                    <i class="bi bi-check"></i>
                  </button>
                  <button class="btn btn-sm btn-outline-danger" data-bs-toggle="modal" data-bs-target="#rejectModal{{ doc.id }}">
                    <i class="bi bi-x"></i>
                  </button>
                </div>
              </td>
            </tr>
            {% empty %}
            <tr>
              <td colspan="7" class="text-center">Aucun document trouvé</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>
{% endblock %}'''

# Appointments (rendezvous) template
rendezvous_html = '''{% extends 'admin/base.html' %}
{% load static %}

{% block title %}Gestion des Rendez-vous | Administration{% endblock %}

{% block content %}
<div class="container-fluid">
  <div class="d-flex justify-content-between align-items-center mb-4">
    <h1 class="h2">Gestion des Rendez-vous</h1>
  </div>

  <!-- Statistics Row -->
  <div class="row mb-4">
    <div class="col-md-3">
      <div class="stats-card">
        <div class="icon text-primary">
          <i class="bi bi-calendar"></i>
        </div>
        <div class="count">{{ stats.total }}</div>
        <div class="title">Total Rendez-vous</div>
      </div>
    </div>
    
    <div class="col-md-3">
      <div class="stats-card">
        <div class="icon text-warning">
          <i class="bi bi-calendar-check"></i>
        </div>
        <div class="count">{{ stats.upcoming }}</div>
        <div class="title">À venir</div>
      </div>
    </div>
    
    <div class="col-md-3">
      <div class="stats-card">
        <div class="icon text-success">
          <i class="bi bi-calendar2-check"></i>
        </div>
        <div class="count">{{ stats.completed }}</div>
        <div class="title">Complétés</div>
      </div>
    </div>
    
    <div class="col-md-3">
      <div class="stats-card">
        <div class="icon text-danger">
          <i class="bi bi-calendar-x"></i>
        </div>
        <div class="count">{{ stats.cancelled }}</div>
        <div class="title">Annulés</div>
      </div>
    </div>
  </div>

  <!-- Filter Section -->
  <div class="filter-section mb-4">
    <form method="get" class="row g-3">
      <div class="col-md-3">
        <label for="expert" class="form-label">Expert</label>
        <select id="expert" name="expert" class="form-select">
          <option value="">Tous les experts</option>
          {% for exp in experts %}
          <option value="{{ exp.id }}" {% if expert_id|stringformat:"s" == exp.id|stringformat:"s" %}selected{% endif %}>
            {{ exp.user.first_name }} {{ exp.user.name }}
          </option>
          {% endfor %}
        </select>
      </div>
      
      <div class="col-md-3">
        <label for="client" class="form-label">Client</label>
        <select id="client" name="client" class="form-select">
          <option value="">Tous les clients</option>
          {% for cl in clients %}
          <option value="{{ cl.id }}" {% if client_id|stringformat:"s" == cl.id|stringformat:"s" %}selected{% endif %}>
            {{ cl.user.first_name }} {{ cl.user.name }}
          </option>
          {% endfor %}
        </select>
      </div>
      
      <div class="col-md-2">
        <label for="date" class="form-label">Date</label>
        <select id="date" name="date" class="form-select">
          <option value="">Toutes les dates</option>
          <option value="today" {% if date_filter == 'today' %}selected{% endif %}>Aujourd'hui</option>
          <option value="tomorrow" {% if date_filter == 'tomorrow' %}selected{% endif %}>Demain</option>
          <option value="week" {% if date_filter == 'week' %}selected{% endif %}>Cette semaine</option>
        </select>
      </div>
      
      <div class="col-md-2">
        <label for="status" class="form-label">Statut</label>
        <select id="status" name="status" class="form-select">
          <option value="">Tous</option>
          <option value="confirmed" {% if status_filter == 'confirmed' %}selected{% endif %}>Confirmé</option>
          <option value="completed" {% if status_filter == 'completed' %}selected{% endif %}>Complété</option>
          <option value="cancelled" {% if status_filter == 'cancelled' %}selected{% endif %}>Annulé</option>
        </select>
      </div>
      
      <div class="col-md-2 d-flex align-items-end">
        <button type="submit" class="btn btn-primary w-100">
          <i class="bi bi-filter"></i> Filtrer
        </button>
      </div>
    </form>
  </div>

  <!-- Appointments List -->
  <div class="card">
    <div class="card-header bg-white">
      <h5 class="card-title mb-0">Liste des Rendez-vous</h5>
    </div>
    <div class="card-body">
      <div class="table-responsive">
        <table class="table table-hover">
          <thead>
            <tr>
              <th>Client</th>
              <th>Expert</th>
              <th>Date / Heure</th>
              <th>Service</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {% for appointment in appointments %}
            <tr>
              <td>{{ appointment.client.user.first_name }} {{ appointment.client.user.name }}</td>
              <td>{{ appointment.expert.user.first_name }} {{ appointment.expert.user.name }}</td>
              <td>{{ appointment.date|date:"d/m/Y" }} à {{ appointment.time }}</td>
              <td>{{ appointment.request.service.name }}</td>
              <td>
                {% if appointment.status == 'confirmed' %}
                <span class="badge bg-primary">Confirmé</span>
                {% elif appointment.status == 'completed' %}
                <span class="badge bg-success">Complété</span>
                {% elif appointment.status == 'cancelled' %}
                <span class="badge bg-danger">Annulé</span>
                {% else %}
                <span class="badge bg-warning">En attente</span>
                {% endif %}
              </td>
              <td>
                <div class="btn-group">
                  <button class="btn btn-sm btn-outline-primary" data-bs-toggle="modal" data-bs-target="#viewAppointmentModal{{ appointment.id }}">
                    <i class="bi bi-eye"></i>
                  </button>
                  <button class="btn btn-sm btn-outline-success" data-bs-toggle="modal" data-bs-target="#completeModal{{ appointment.id }}">
                    <i class="bi bi-check"></i>
                  </button>
                  <button class="btn btn-sm btn-outline-danger" data-bs-toggle="modal" data-bs-target="#cancelModal{{ appointment.id }}">
                    <i class="bi bi-x"></i>
                  </button>
                </div>
              </td>
            </tr>
            {% empty %}
            <tr>
              <td colspan="6" class="text-center">Aucun rendez-vous trouvé</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>
{% endblock %}'''

# Resources (ressources) template
ressources_html = '''{% extends 'admin/base.html' %}
{% load static %}

{% block title %}Gestion des Ressources | Administration{% endblock %}

{% block content %}
<div class="container-fluid">
  <div class="d-flex justify-content-between align-items-center mb-4">
    <h1 class="h2">Gestion des Ressources</h1>
    <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addResourceModal">
      <i class="bi bi-plus-circle"></i> Ajouter une ressource
    </button>
  </div>

  <!-- Statistics Row -->
  <div class="row mb-4">
    <div class="col-md-4">
      <div class="stats-card">
        <div class="icon text-primary">
          <i class="bi bi-book"></i>
        </div>
        <div class="count">{{ stats.total }}</div>
        <div class="title">Total Ressources</div>
      </div>
    </div>
    
    <div class="col-md-4">
      <div class="stats-card">
        <div class="icon text-success">
          <i class="bi bi-eye"></i>
        </div>
        <div class="count">{{ stats.public }}</div>
        <div class="title">Ressources Publiques</div>
      </div>
    </div>
    
    <div class="col-md-4">
      <div class="stats-card">
        <div class="icon text-warning">
          <i class="bi bi-eye-slash"></i>
        </div>
        <div class="count">{{ stats.private }}</div>
        <div class="title">Ressources Privées</div>
      </div>
    </div>
  </div>

  <!-- Filter Section -->
  <div class="filter-section mb-4">
    <form method="get" class="row g-3">
      <div class="col-md-4">
        <label for="category" class="form-label">Catégorie</label>
        <select id="category" name="category" class="form-select">
          <option value="">Toutes les catégories</option>
          {% for cat in categories %}
          <option value="{{ cat }}" {% if category == cat %}selected{% endif %}>{{ cat }}</option>
          {% endfor %}
        </select>
      </div>
      
      <div class="col-md-3">
        <label for="visibility" class="form-label">Visibilité</label>
        <select id="visibility" name="visibility" class="form-select">
          <option value="">Toutes</option>
          <option value="public" {% if visibility == 'public' %}selected{% endif %}>Publique</option>
          <option value="private" {% if visibility == 'private' %}selected{% endif %}>Privée</option>
        </select>
      </div>
      
      <div class="col-md-3">
        <label for="search" class="form-label">Recherche</label>
        <input type="text" class="form-control" id="search" name="search" placeholder="Titre ou description..." value="{{ search_query }}">
      </div>
      
      <div class="col-md-2 d-flex align-items-end">
        <button type="submit" class="btn btn-primary w-100">
          <i class="bi bi-filter"></i> Filtrer
        </button>
      </div>
    </form>
  </div>

  <!-- Resources List -->
  <div class="card">
    <div class="card-header bg-white">
      <h5 class="card-title mb-0">Liste des Ressources</h5>
    </div>
    <div class="card-body">
      <div class="row">
        {% for resource in resources %}
        <div class="col-md-4 mb-4">
          <div class="card h-100">
            {% if resource.thumbnail %}
            <img src="{{ resource.thumbnail.url }}" class="card-img-top" alt="{{ resource.title }}">
            {% else %}
            <div class="card-img-top bg-light d-flex align-items-center justify-content-center" style="height: 150px;">
              <i class="bi bi-file-earmark text-muted" style="font-size: 3rem;"></i>
            </div>
            {% endif %}
            <div class="card-body">
              <h5 class="card-title">{{ resource.title }}</h5>
              <p class="card-text small">{{ resource.description|truncatechars:100 }}</p>
              <div class="d-flex justify-content-between align-items-center">
                <span class="badge {% if resource.is_public %}bg-success{% else %}bg-warning{% endif %}">
                  {% if resource.is_public %}Public{% else %}Privé{% endif %}
                </span>
                <small class="text-muted">{{ resource.created_at|date:"d/m/Y" }}</small>
              </div>
            </div>
            <div class="card-footer bg-white">
              <div class="btn-group w-100">
                {% if resource.file %}
                <a href="{{ resource.file.url }}" target="_blank" class="btn btn-sm btn-outline-primary">
                  <i class="bi bi-download"></i> Télécharger
                </a>
                {% endif %}
                <button class="btn btn-sm btn-outline-secondary" data-bs-toggle="modal" data-bs-target="#editResourceModal{{ resource.id }}">
                  <i class="bi bi-pencil"></i> Modifier
                </button>
                <button class="btn btn-sm btn-outline-danger" data-bs-toggle="modal" data-bs-target="#deleteResourceModal{{ resource.id }}">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
        {% empty %}
        <div class="col-12 text-center py-5">
          <i class="bi bi-exclamation-circle text-muted" style="font-size: 3rem;"></i>
          <p class="text-muted mt-3">Aucune ressource trouvée</p>
        </div>
        {% endfor %}
      </div>
    </div>
  </div>
</div>
{% endblock %}'''

# Messages template
messages_html = '''{% extends 'admin/base.html' %}
{% load static %}

{% block title %}Gestion des Messages | Administration{% endblock %}

{% block content %}
<div class="container-fluid">
  <div class="d-flex justify-content-between align-items-center mb-4">
    <h1 class="h2">Gestion des Messages</h1>
  </div>

  <!-- Statistics Row -->
  <div class="row mb-4">
    <div class="col-md-6">
      <div class="stats-card">
        <div class="icon text-primary">
          <i class="bi bi-chat-dots"></i>
        </div>
        <div class="count">{{ stats.total }}</div>
        <div class="title">Total Messages</div>
      </div>
    </div>
    
    <div class="col-md-6">
      <div class="stats-card">
        <div class="icon text-warning">
          <i class="bi bi-envelope"></i>
        </div>
        <div class="count">{{ stats.unread }}</div>
        <div class="title">Messages Non Lus</div>
      </div>
    </div>
  </div>

  <!-- Filter Section -->
  <div class="filter-section mb-4">
    <form method="get" class="row g-3">
      <div class="col-md-3">
        <label for="client" class="form-label">Client</label>
        <select id="client" name="client" class="form-select">
          <option value="">Tous les clients</option>
          {% for client in clients %}
          <option value="{{ client.id }}" {% if client_id|stringformat:"s" == client.id|stringformat:"s" %}selected{% endif %}>
            {{ client.user.first_name }} {{ client.user.name }}
          </option>
          {% endfor %}
        </select>
      </div>
      
      <div class="col-md-3">
        <label for="expert" class="form-label">Expert</label>
        <select id="expert" name="expert" class="form-select">
          <option value="">Tous les experts</option>
          {% for expert in experts %}
          <option value="{{ expert.id }}" {% if expert_id|stringformat:"s" == expert.id|stringformat:"s" %}selected{% endif %}>
            {{ expert.user.first_name }} {{ expert.user.name }}
          </option>
          {% endfor %}
        </select>
      </div>
      
      <div class="col-md-2">
        <label for="read-status" class="form-label">Statut</label>
        <select id="read-status" name="read_status" class="form-select">
          <option value="">Tous</option>
          <option value="read" {% if read_status == 'read' %}selected{% endif %}>Lu</option>
          <option value="unread" {% if read_status == 'unread' %}selected{% endif %}>Non lu</option>
        </select>
      </div>
      
      <div class="col-md-2">
        <label for="search" class="form-label">Recherche</label>
        <input type="text" class="form-control" id="search" name="search" placeholder="Contenu..." value="{{ search_query }}">
      </div>
      
      <div class="col-md-2 d-flex align-items-end">
        <button type="submit" class="btn btn-primary w-100">
          <i class="bi bi-filter"></i> Filtrer
        </button>
      </div>
    </form>
  </div>

  <!-- Messages List -->
  <div class="card">
    <div class="card-header bg-white">
      <h5 class="card-title mb-0">Liste des Messages</h5>
    </div>
    <div class="card-body">
      <div class="table-responsive">
        <table class="table table-hover">
          <thead>
            <tr>
              <th>Expéditeur</th>
              <th>Destinataire</th>
              <th>Contenu</th>
              <th>Date d'envoi</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {% for message in messages %}
            <tr>
              <td>{{ message.sender.first_name }} {{ message.sender.name }}</td>
              <td>{{ message.receiver.first_name }} {{ message.receiver.name }}</td>
              <td>{{ message.content|truncatechars:50 }}</td>
              <td>{{ message.sent_at|date:"d/m/Y H:i" }}</td>
              <td>
                {% if message.is_read %}
                <span class="badge bg-success">Lu</span>
                {% else %}
                <span class="badge bg-warning">Non lu</span>
                {% endif %}
              </td>
              <td>
                <div class="btn-group">
                  <button class="btn btn-sm btn-outline-primary" data-bs-toggle="modal" data-bs-target="#viewMessageModal{{ message.id }}">
                    <i class="bi bi-eye"></i>
                  </button>
                  <button class="btn btn-sm btn-outline-danger" data-bs-toggle="modal" data-bs-target="#deleteMessageModal{{ message.id }}">
                    <i class="bi bi-trash"></i>
                  </button>
                </div>
              </td>
            </tr>
            {% empty %}
            <tr>
              <td colspan="6" class="text-center">Aucun message trouvé</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>
{% endblock %}'''

# Write the files
import os

base_dir = r'c:\Users\Airzo\Desktop\My Website\ServiceBladiTest2\ServicesBLADI V6\ServicesBLADIV3\frontend\template\admin'

# Make sure the directory exists
if not os.path.exists(base_dir):
    os.makedirs(base_dir)

# Write user template
with open(os.path.join(base_dir, 'users.html'), 'w', encoding='utf-8') as f:
    f.write(users_html)

# Write documents template
with open(os.path.join(base_dir, 'documents.html'), 'w', encoding='utf-8') as f:
    f.write(documents_html)

# Write rendezvous template
with open(os.path.join(base_dir, 'rendezvous.html'), 'w', encoding='utf-8') as f:
    f.write(rendezvous_html)

# Write ressources template
with open(os.path.join(base_dir, 'ressources.html'), 'w', encoding='utf-8') as f:
    f.write(ressources_html)

# Write messages template
with open(os.path.join(base_dir, 'messages.html'), 'w', encoding='utf-8') as f:
    f.write(messages_html)

print("All admin templates have been created successfully!")
