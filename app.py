"""
Flask Web Application for DB2 Query Performance Testing
"""

from flask import Flask, render_template, jsonify, request
import json
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.db_connection import DB2Connection
from src.queries import QueryTypes, QUERY_DESCRIPTIONS
from src.performance_monitor import QueryPerformanceTracker, format_performance_report, format_comparison_report

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Global instances
db = DB2Connection()
tracker = QueryPerformanceTracker()


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/connect', methods=['POST'])
def connect_db():
    """Connect to database"""
    try:
        if db.connect():
            stats = db.get_table_stats()
            pending_count = db.get_pending_applications_count()
            
            return jsonify({
                'success': True,
                'message': 'Connected to DB2 successfully!',
                'stats': stats,
                'pending_applications': pending_count
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to connect to database'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/disconnect', methods=['POST'])
def disconnect_db():
    """Disconnect from database"""
    try:
        db.disconnect()
        return jsonify({
            'success': True,
            'message': 'Disconnected successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        if not db.is_connected():
            return jsonify({
                'success': False,
                'message': 'Not connected to database'
            }), 400
        
        stats = db.get_table_stats()
        pending_count = db.get_pending_applications_count()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'pending_applications': pending_count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/execute/<query_type>', methods=['POST'])
def execute_query(query_type):
    """Execute a query and measure performance"""
    try:
        if not db.is_connected():
            return jsonify({
                'success': False,
                'message': 'Not connected to database. Please connect first.'
            }), 400
        
        # Get the appropriate query
        if query_type == 'update_subquery':
            query = QueryTypes.get_update_with_subquery()
            query_name = QUERY_DESCRIPTIONS['update_subquery']['name']
        elif query_type == 'merge':
            query = QueryTypes.get_merge_query()
            query_name = QUERY_DESCRIPTIONS['merge']['name']
        else:
            return jsonify({
                'success': False,
                'message': f'Invalid query type: {query_type}'
            }), 400
        
        # Execute and measure
        result = tracker.execute_and_measure(
            query_name,
            db.execute_query,
            query
        )
        
        # Get comparison if we have multiple results
        comparison = None
        if len(tracker.get_all_results()) >= 2:
            comparison = tracker.get_comparison()
        
        return jsonify({
            'success': True,
            'result': result,
            'comparison': comparison
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/reset', methods=['POST'])
def reset_data():
    """Reset test data"""
    try:
        if not db.is_connected():
            return jsonify({
                'success': False,
                'message': 'Not connected to database'
            }), 400
        
        rows_affected = db.reset_test_data()
        
        return jsonify({
            'success': True,
            'message': f'Reset {rows_affected:,} applications to PENDING status',
            'rows_affected': rows_affected
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/clear-results', methods=['POST'])
def clear_results():
    """Clear performance results"""
    tracker.clear_results()
    return jsonify({
        'success': True,
        'message': 'Results cleared'
    })


@app.route('/api/results', methods=['GET'])
def get_results():
    """Get all performance results"""
    results = tracker.get_all_results()
    comparison = None
    
    if len(results) >= 2:
        comparison = tracker.get_comparison()
    
    return jsonify({
        'success': True,
        'results': results,
        'comparison': comparison
    })


@app.route('/api/query-info', methods=['GET'])
def get_query_info():
    """Get information about available queries"""
    return jsonify({
        'success': True,
        'queries': QUERY_DESCRIPTIONS
    })


if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    print(f"\n{'='*60}")
    print(f"DB2 Query Performance Testing - Web Interface")
    print(f"{'='*60}")
    print(f"\nStarting Flask server on http://localhost:{port}")
    print(f"Make sure DB2 container is running: docker-compose up -d")
    print(f"\n{'='*60}\n")
    
    app.run(debug=True, host='0.0.0.0', port=port)
