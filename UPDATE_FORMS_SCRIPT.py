"""
Script de mise à jour automatique de tous les formulaires
Ce script identifie tous les champs de formulaires et ajoute la validation
"""

# Ce fichier sert de documentation pour la mise à jour des formulaires
# Chaque formulaire suit le même pattern

PATTERN_FIELD = """
<div>
    <label for="{field_id}" class="block text-sm font-medium text-gray-700 mb-2">
        {label} {% if required %}<span class="text-red-500">*</span>{% endif %}
    </label>
    <{input_tag} 
        type="{input_type}" 
        name="{field_name}" 
        id="{field_id}"
        {% if required %}required{% endif %}
        value="{{ request.POST.{field_name}|default:'' }}"
        placeholder="{placeholder}"
        class="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:border-transparent transition
               {% if form.{field_name}.errors %}border-red-500 focus:ring-red-500 bg-red-50{% else %}border-gray-300 focus:ring-lily-purple{% endif %}"
    >
    {% if form.{field_name}.errors %}
        <div class="mt-2 space-y-1">
            {% for error in form.{field_name}.errors %}
                <p class="text-sm text-red-600 flex items-start">
                    <svg class="w-4 h-4 mr-1 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                    </svg>
                    <span>{{ error }}</span>
                </p>
            {% endfor %}
        </div>
    {% endif %}
</div>
"""

# Formulaires à mettre à jour:
FORMULAIRES = {
    'accounts': [
        'login.html',  # FAIT
        'register.html',  # À FAIRE
        'profile.html',  # À FAIRE
    ],
    'projects': [
        'project_create.html',  # EN COURS
        'project_edit.html',  # À FAIRE
    ],
    'proposals': [
        'create_proposal.html',  # À FAIRE
        'send_request.html',  # À FAIRE
    ],
    'messaging': [
        'conversation_detail.html',  # À FAIRE
    ],
    'vendors': [
        'profile_edit.html',  # À FAIRE si existe
    ],
}
