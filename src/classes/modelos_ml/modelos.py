# ----------------------------------------------------------------------------------------------
# Algumas classes que representam modelos para realização de tarefas de Machine Learning
#
# ATENÇÃO: Se uma nova classe for criada ou modificada e houver a necessidade de persisti-la
# em banco de dados, implemente ou altere a sua entrada na rotina da função de desserialização
# no arquivo src.classes.persistencia.serializacao.py
# ----------------------------------------------------------------------------------------------

from sklearn.base import BaseEstimator, ClassifierMixin
# from sklearn import preprocessing
# from tensorflow.keras.preprocessing.text import Tokenizer


class ModeloClassificacao(BaseEstimator, ClassifierMixin):
    """
    Modelo para classificação
    """
    def __init__(self, codigo_modelo):
        self.__codigo_modelo = codigo_modelo
        self.__clf = None  # Vai guardar o modelo escolhido
        self.__nome = ''
        self.__t = Tokenizer(oov_token='***UNK***')
        self.__le = preprocessing.LabelEncoder()

        if self.__codigo_modelo == 1:
            from sklearn.linear_model import SGDClassifier
            from sklearn.preprocessing import StandardScaler
            from sklearn.pipeline import make_pipeline
            self.__nome = 'SGDClassifier'
            self.__clf = make_pipeline(StandardScaler(), SGDClassifier(max_iter=1000, tol=1e-3, loss='log', n_jobs=-1))
        elif self.__codigo_modelo == 2:
            from sklearn.tree import DecisionTreeClassifier
            self.__nome = 'DecisionTreeClassifier'
            self.__clf = DecisionTreeClassifier(random_state=0)
        elif self.__codigo_modelo == 3:
            from sklearn.ensemble import RandomForestClassifier
            self.__nome = 'RandomForestClassifier'
            self.__clf = RandomForestClassifier(random_state=0, n_jobs=-1)
        elif self.__codigo_modelo == 4:
            from sklearn.ensemble import GradientBoostingClassifier
            self.__nome = 'GradientBoostingClassifier'
            self.__clf = GradientBoostingClassifier(n_estimators=100, learning_rate=1.0, random_state=0)
        elif self.__codigo_modelo == 5:
            from sklearn.naive_bayes import MultinomialNB
            self.__nome = 'MultinomialNB'
            self.__clf = MultinomialNB()
        elif self.__codigo_modelo == 6:
            from sklearn.pipeline import make_pipeline
            from sklearn.preprocessing import StandardScaler
            from sklearn.svm import SVC
            self.__nome = 'SVC'
            self.__clf = make_pipeline(StandardScaler(), SVC(gamma='auto'))
        elif self.__codigo_modelo == 7:
            from sklearn.neural_network import MLPClassifier
            self.__nome = 'MLPClassifier'
            self.__clf = MLPClassifier(random_state=1, max_iter=300)
        elif self.__codigo_modelo == 8:
            import xgboost as xgb
            self.__nome = 'xgboost'
            self.__clf = xgb.XGBClassifier(use_label_encoder=False, max_depth=3, n_estimators=300,
                                           learning_rate=0.05, eval_metric='mlogloss')

    @property
    def nome(self):
        return self.__nome

    @property
    def codigo_modelo(self):
        return self.__codigo_modelo

    def fit(self, x_train, y_train):
        # Tokenização dos documentos (Será utilizado somente o x_train para que a fase do treinamento não seja
        # contaminada com dados das fases de validação e teste)
        self.__t.fit_on_texts(x_train)

        # Codifica o texto com base no TF-IDF (Term Frequency - Inverse Document Frequency) que leva em conta a
        # relevância da palavra no texto
        doc_codificados_x_train = self.__t.texts_to_matrix(x_train, mode='tfidf')

        # Transforma os rótulos em números
        # Obs.: Tem que fazer o fit com o y inteiro, para que o transform retorne os mesmos números para y_train, y_test
        self.__le.fit(y_train)
        y_train_labels = self.__le.transform(y_train)

        self.__clf.fit(doc_codificados_x_train, y_train_labels)

    def predict(self, x):
        doc_codificados_x = self.__t.texts_to_matrix(x, mode='tfidf')

        if doc_codificados_x.shape[0] > 0:
            ypred = self.__clf.predict(doc_codificados_x)

            # Retorna o y predito com os rótulos no formato original
            return list(self.__le.inverse_transform(ypred))
        else:
            return []
