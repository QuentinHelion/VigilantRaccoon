#!/usr/bin/env python3
"""
Script principal pour exécuter tous les tests unitaires de VigilantRaccoon
"""

import sys
import os
import unittest
import time
from pathlib import Path

# Ajout du répertoire racine au path Python
sys.path.insert(0, str(Path(__file__).parent))

def run_test_suite():
    """Exécute la suite complète de tests"""
    print("🧪 Démarrage des tests unitaires de VigilantRaccoon")
    print("=" * 60)
    
    # Découverte automatique des tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent / "tests"
    
    if not start_dir.exists():
        print(f"❌ Répertoire de tests non trouvé: {start_dir}")
        return False
    
    # Découverte des tests
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    # Exécution des tests
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # Affichage des résultats
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS DES TESTS")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    
    print(f"✅ Tests exécutés: {total_tests}")
    print(f"❌ Échecs: {failures}")
    print(f"⚠️  Erreurs: {errors}")
    print(f"⏭️  Ignorés: {skipped}")
    print(f"⏱️  Temps d'exécution: {end_time - start_time:.2f} secondes")
    
    if failures > 0:
        print(f"\n🚨 DÉTAILS DES ÉCHECS:")
        for test, traceback in result.failures:
            print(f"   • {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if errors > 0:
        print(f"\n💥 DÉTAILS DES ERREURS:")
        for test, traceback in result.errors:
            print(f"   • {test}: {traceback.split('Error:')[-1].strip()}")
    
    # Résumé final
    print("\n" + "=" * 60)
    if failures == 0 and errors == 0:
        print("🎉 TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS!")
        success = True
    else:
        print("⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
        success = False
    
    print("=" * 60)
    
    return success


def run_specific_test(test_name):
    """Exécute un test spécifique"""
    print(f"🧪 Exécution du test spécifique: {test_name}")
    print("=" * 60)
    
    # Découverte du test spécifique
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent / "tests"
    
    if not start_dir.exists():
        print(f"❌ Répertoire de tests non trouvé: {start_dir}")
        return False
    
    # Recherche du test
    suite = loader.discover(start_dir, pattern=f"test_{test_name}.py")
    
    if not suite.countTestCases():
        print(f"❌ Aucun test trouvé pour: {test_name}")
        return False
    
    # Exécution du test
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return len(result.failures) == 0 and len(result.errors) == 0


def list_available_tests():
    """Liste tous les tests disponibles"""
    print("📋 TESTS DISPONIBLES")
    print("=" * 60)
    
    tests_dir = Path(__file__).parent / "tests"
    
    if not tests_dir.exists():
        print("❌ Aucun test trouvé")
        return
    
    test_files = list(tests_dir.glob("test_*.py"))
    
    if not test_files:
        print("❌ Aucun fichier de test trouvé")
        return
    
    for test_file in sorted(test_files):
        test_name = test_file.stem.replace("test_", "")
        print(f"   • {test_name}")
    
    print(f"\nTotal: {len(test_files)} tests disponibles")
    print("\nPour exécuter un test spécifique:")
    print(f"   python {__file__} --test <nom_du_test>")
    print(f"   Exemple: python {__file__} --test domain_entities")


def main():
    """Fonction principale"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("Usage:")
            print(f"  python {__file__}                    # Exécute tous les tests")
            print(f"  python {__file__} --test <nom>       # Exécute un test spécifique")
            print(f"  python {__file__} --list             # Liste tous les tests disponibles")
            print(f"  python {__file__} --help             # Affiche cette aide")
            return
        
        elif sys.argv[1] == "--list" or sys.argv[1] == "-l":
            list_available_tests()
            return
        
        elif sys.argv[1] == "--test" or sys.argv[1] == "-t":
            if len(sys.argv) < 3:
                print("❌ Nom du test manquant")
                print(f"Usage: python {__file__} --test <nom_du_test>")
                return
            
            test_name = sys.argv[2]
            success = run_specific_test(test_name)
            sys.exit(0 if success else 1)
        
        else:
            print(f"❌ Option inconnue: {sys.argv[1]}")
            print(f"Utilisez --help pour voir les options disponibles")
            sys.exit(1)
    
    # Exécution de tous les tests par défaut
    success = run_test_suite()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 