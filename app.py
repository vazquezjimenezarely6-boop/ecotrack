from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'clave_simple'

# Datos en memoria (más simple que archivos)
data = {
    'recycling_items': [],
    'total_points': 0,
    'total_items': 0
}

categories = {
    'plastic': {'name': 'Plástico', 'points': 10, 'color': '#007bff'},
    'paper': {'name': 'Papel', 'points': 8, 'color': '#28a745'},
    'glass': {'name': 'Vidrio', 'points': 12, 'color': '#fd7e14'},
    'metal': {'name': 'Metal', 'points': 15, 'color': '#6f42c1'},
    'organic': {'name': 'Orgánico', 'points': 5, 'color': '#795548'},
    'electronic': {'name': 'Electrónico', 'points': 20, 'color': '#dc3545'}
}

@app.route('/')
def index():
    recent_items = data['recycling_items'][-5:][::-1] if data['recycling_items'] else []
    
    # Calcular estadísticas para el dashboard
    stats = {
        'total_items': data['total_items'],
        'total_points': data['total_points'],
        'level': data['total_points'] // 100 + 1,
        'recent_activity': recent_items
    }
    
    return render_template('index.html', 
                         data=stats, 
                         categories=categories,
                         recent_items=recent_items)

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        category = request.form.get('category')
        quantity = int(request.form.get('quantity', 1))
        description = request.form.get('description', '')
        
        if category in categories:
            points = categories[category]['points'] * quantity
            
            new_item = {
                'id': len(data['recycling_items']) + 1,
                'category': category,
                'category_name': categories[category]['name'],
                'quantity': quantity,
                'description': description,
                'points': points,
                'timestamp': datetime.now().isoformat(),
                'date': datetime.now().strftime('%Y-%m-%d')
            }
            
            data['recycling_items'].append(new_item)
            data['total_points'] += points
            data['total_items'] += quantity
            
            flash('¡Reciclaje registrado correctamente! +{} puntos'.format(points), 'success')
            return redirect(url_for('index'))
        else:
            flash('Error: Por favor selecciona una categoría válida', 'error')
    
    return render_template('create.html', categories=categories)

@app.route('/statistics')
def statistics():
    # Calcular distribución por material
    material_distribution = {}
    for item in data['recycling_items']:
        category = item['category']
        if category not in material_distribution:
            material_distribution[category] = 0
        material_distribution[category] += item['quantity']
    
    # Preparar datos para gráficos
    materials_data = {
        'materials': [],
        'quantities': [],
        'colors': []
    }
    
    for category, quantity in material_distribution.items():
        materials_data['materials'].append(categories[category]['name'])
        materials_data['quantities'].append(quantity)
        materials_data['colors'].append(categories[category]['color'])
    
    stats = {
        'total_items': data['total_items'],
        'total_points': data['total_points'],
        'material_distribution': material_distribution,
        'materials_data': materials_data
    }
    
    return render_template('statistics.html', 
                         data=stats, 
                         categories=categories,
                         materials_data=materials_data)

@app.route('/achievements')
def achievements():
    # Definir logros
    achievements_list = [
        {
            'name': '🌱 Primer Paso', 
            'description': 'Registra tu primer reciclaje', 
            'icon': 'fas fa-seedling',
            'points': 10,
            'unlocked': len(data['recycling_items']) > 0,
            'progress': 100 if len(data['recycling_items']) > 0 else 0
        },
        {
            'name': '⭐ Novato Ecológico', 
            'description': 'Alcanza 50 puntos', 
            'icon': 'fas fa-star',
            'points': 25,
            'unlocked': data['total_points'] >= 50,
            'progress': min((data['total_points'] / 50) * 100, 100)
        },
        {
            'name': '🏆 Guerrero Verde', 
            'description': 'Alcanza 100 puntos', 
            'icon': 'fas fa-trophy',
            'points': 50,
            'unlocked': data['total_points'] >= 100,
            'progress': min((data['total_points'] / 100) * 100, 100)
        },
        {
            'name': '👑 Héroe del Planeta', 
            'description': 'Alcanza 250 puntos', 
            'icon': 'fas fa-crown',
            'points': 100,
            'unlocked': data['total_points'] >= 250,
            'progress': min((data['total_points'] / 250) * 100, 100)
        }
    ]
    
    unlocked_achievements = [a for a in achievements_list if a['unlocked']]
    locked_achievements = [a for a in achievements_list if not a['unlocked']]
    
    return render_template('achievements.html',
                         unlocked_achievements=unlocked_achievements,
                         locked_achievements=locked_achievements,
                         unlocked_count=len(unlocked_achievements),
                         total_achievements=len(achievements_list),
                         data={'total_points': data['total_points'], 
                              'total_items': data['total_items'],
                              'level': data['total_points'] // 100 + 1})

@app.route('/tips')
def tips():
    return render_template('tips.html', 
                         data={'total_points': data['total_points'], 
                              'total_items': data['total_items']})

@app.route('/view/<int:id>')
def view(id):
    record = next((item for item in data['recycling_items'] if item['id'] == id), None)
    if not record:
        flash('Registro no encontrado', 'error')
        return redirect(url_for('index'))
    
    return render_template('view.html', 
                         record=record, 
                         categories=categories)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    record = next((item for item in data['recycling_items'] if item['id'] == id), None)
    if not record:
        flash('Registro no encontrado', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        quantity = int(request.form.get('quantity', 1))
        description = request.form.get('description', '')
        
        # Calcular nueva puntuación
        old_points = record['points']
        record['quantity'] = quantity
        record['description'] = description
        record['points'] = categories[record['category']]['points'] * quantity
        
        # Actualizar totales
        points_diff = record['points'] - old_points
        data['total_points'] += points_diff
        data['total_items'] += (quantity - record['quantity'])
        
        flash('Registro actualizado correctamente', 'success')
        return redirect(url_for('index'))
    
    return render_template('edit.html', 
                         record=record, 
                         categories=categories)

@app.route('/delete/<int:id>')
def delete(id):
    global data
    record = next((item for item in data['recycling_items'] if item['id'] == id), None)
    if record:
        data['recycling_items'] = [item for item in data['recycling_items'] if item['id'] != id]
        data['total_points'] -= record['points']
        data['total_items'] -= record['quantity']
        flash('Registro eliminado correctamente', 'success')
    else:
        flash('Registro no encontrado', 'error')
    
    return redirect(url_for('index'))

# APIs
@app.route('/api/stats')
def api_stats():
    return jsonify({
        'total_items': data['total_items'],
        'total_points': data['total_points'],
        'level': data['total_points'] // 100 + 1
    })

@app.route('/api/recent-activity')
def api_recent_activity():
    return jsonify(data['recycling_items'][-10:][::-1])

@app.route('/api/materials-data')
def api_materials_data():
    material_distribution = {}
    for item in data['recycling_items']:
        category = item['category']
        if category not in material_distribution:
            material_distribution[category] = 0
        material_distribution[category] += item['quantity']
    
    materials_data = {
        'materials': [],
        'quantities': [],
        'colors': []
    }
    
    for category, quantity in material_distribution.items():
        materials_data['materials'].append(categories[category]['name'])
        materials_data['quantities'].append(quantity)
        materials_data['colors'].append(categories[category]['color'])
    
    # Si no hay datos, devolver datos de ejemplo vacíos
    if not materials_data['materials']:
        materials_data = {
            'materials': ['Plástico', 'Papel', 'Vidrio', 'Metal', 'Orgánico', 'Electrónico'],
            'quantities': [0, 0, 0, 0, 0, 0],
            'colors': ['#007bff', '#28a745', '#fd7e14', '#6f42c1', '#795548', '#dc3545']
        }
    
    return jsonify(materials_data)

if __name__ == '__main__':
    print("🚀 EcoTrack INICIADO: http://localhost:5000")
    print("📊 Funcionalidades: Dashboard, Registrar, Estadísticas, Logros, Consejos")
    app.run(debug=True, port=5000)