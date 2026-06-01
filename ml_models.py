import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os

class DocumentClassifier:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='spanish')
        self.classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        self.model_path = 'models/document_classifier.pkl'
        
        # Try to load existing model
        if os.path.exists(self.model_path):
            self.load_model()
    
    def train(self, documents, labels):
        """
        Entrena el clasificador de documentos
        documents: lista de textos de documentos
        labels: lista de etiquetas (tipos de documento)
        """
        # Vectorizar documentos
        X = self.vectorizer.fit_transform(documents)
        
        # Codificar etiquetas
        y = self.label_encoder.fit_transform(labels)
        
        # Entrenar clasificador
        self.classifier.fit(X, y)
        self.is_trained = True
        
        # Guardar modelo
        self.save_model()
    
    def predict(self, document_text):
        """
        Predice el tipo de documento
        document_text: texto del documento a clasificar
        """
        if not self.is_trained:
            # Si no está entrenado, usar clasificación basada en reglas simples
            return self._rule_based_classification(document_text)
        
        # Vectorizar documento
        X = self.vectorizer.transform([document_text])
        
        # Predecir
        prediction = self.classifier.predict(X)[0]
        probability = self.classifier.predict_proba(X)[0].max()
        
        # Decodificar etiqueta
        label = self.label_encoder.inverse_transform([prediction])[0]
        
        return label, probability
    
    def _rule_based_classification(self, text):
        """Clasificación basada en reglas simples cuando el modelo no está entrenado"""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['dni', 'identidad', 'documento nacional']):
            return 'DNI', 0.8
        elif any(keyword in text_lower for keyword in ['curriculum', 'cv', 'experiencia', 'educación']):
            return 'Curriculum', 0.85
        elif any(keyword in text_lower for keyword in ['solicitud', 'petición', 'requerimiento']):
            return 'Solicitud', 0.75
        elif any(keyword in text_lower for keyword in ['certificado', 'constancia']):
            return 'Certificado', 0.8
        elif any(keyword in text_lower for keyword in ['licencia', 'permiso']):
            return 'Licencia', 0.75
        else:
            return 'Documento General', 0.5
    
    def save_model(self):
        """Guarda el modelo entrenado"""
        os.makedirs('models', exist_ok=True)
        model_data = {
            'vectorizer': self.vectorizer,
            'classifier': self.classifier,
            'label_encoder': self.label_encoder
        }
        joblib.dump(model_data, self.model_path)
    
    def load_model(self):
        """Carga el modelo entrenado"""
        try:
            model_data = joblib.load(self.model_path)
            self.vectorizer = model_data['vectorizer']
            self.classifier = model_data['classifier']
            self.label_encoder = model_data['label_encoder']
            self.is_trained = True
        except:
            self.is_trained = False

class PriorityPredictor:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        self.model_path = 'models/priority_predictor.pkl'
        
        # Try to load existing model
        if os.path.exists(self.model_path):
            self.load_model()
    
    def train(self, features, labels):
        """
        Entrena el predictor de prioridad
        features: DataFrame con características del trámite
        labels: lista de prioridades
        """
        # Codificar etiquetas
        y = self.label_encoder.fit_transform(labels)
        
        # Entrenar modelo
        self.model.fit(features, y)
        self.is_trained = True
        
        # Guardar modelo
        self.save_model()
    
    def predict(self, tramite_data):
        """
        Predice la prioridad de un trámite
        tramite_data: diccionario con datos del trámite
        """
        if not self.is_trained:
            # Si no está entrenado, usar reglas de negocio
            return self._rule_based_priority(tramite_data)
        
        # Extraer características
        features = self._extract_features(tramite_data)
        
        # Predecir
        prediction = self.model.predict([features])[0]
        probability = self.model.predict_proba([features])[0].max()
        
        # Decodificar etiqueta
        label = self.label_encoder.inverse_transform([prediction])[0]
        
        return label, probability
    
    def _extract_features(self, tramite_data):
        """Extrae características del trámite para el modelo ML"""
        features = []
        
        # Tipo de trámite (codificado)
        tipo_tramite = tramite_data.get('tipo_tramite', '')
        features.append(len(tipo_tramite))
        
        # Descripción (longitud)
        descripcion = tramite_data.get('descripcion', '')
        features.append(len(descripcion))
        
        # Palabras clave urgentes
        urgent_keywords = ['urgente', 'emergencia', 'inmediato', 'crítico', 'grave']
        text = (tipo_tramite + ' ' + descripcion).lower()
        features.append(sum(1 for keyword in urgent_keywords if keyword in text))
        
        # Número de documentos
        features.append(tramite_data.get('num_documentos', 0))
        
        return features
    
    def _rule_based_priority(self, tramite_data):
        """Asigna prioridad basada en reglas de negocio"""
        tipo_tramite = tramite_data.get('tipo_tramite', '').lower()
        descripcion = tramite_data.get('descripcion', '').lower()
        text = tipo_tramite + ' ' + descripcion
        
        # Palabras clave urgentes
        urgent_keywords = ['urgente', 'emergencia', 'inmediato', 'crítico', 'grave', 'salud', 'seguridad']
        
        if any(keyword in text for keyword in urgent_keywords):
            return 'urgente', 0.9
        elif any(keyword in text for keyword in ['licencia', 'permiso', 'certificado']):
            return 'alta', 0.8
        elif any(keyword in text for keyword in ['solicitud', 'reclamo', 'queja']):
            return 'media', 0.7
        else:
            return 'baja', 0.6
    
    def save_model(self):
        """Guarda el modelo entrenado"""
        os.makedirs('models', exist_ok=True)
        model_data = {
            'model': self.model,
            'label_encoder': self.label_encoder
        }
        joblib.dump(model_data, self.model_path)
    
    def load_model(self):
        """Carga el modelo entrenado"""
        try:
            model_data = joblib.load(self.model_path)
            self.model = model_data['model']
            self.label_encoder = model_data['label_encoder']
            self.is_trained = True
        except:
            self.is_trained = False
