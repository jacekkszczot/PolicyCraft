# !/usr/bin/env python3
"""
Batch analysis of clean university AI policy dataset.
Tests full PolicyCraft pipeline on real university policies.

Author: Jacek Robert Kszczot
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add src to path for imports
sys.path.append('src')

# Import PolicyCraft components
from src.nlp.text_processor import TextProcessor
from src.nlp.theme_extractor import ThemeExtractor
from src.nlp.policy_classifier import PolicyClassifier
from src.database.operations import DatabaseOperations
from src.visualisation.charts import ChartGenerator
from src.recommendation.engine import RecommendationEngine

def run_batch_analysis():
    """Run complete analysis on clean dataset."""
    
    print("🚀 STARTING BATCH ANALYSIS OF CLEAN DATASET")
    print("=" * 60)
    
    # Initialize components
    print("🔧 Initializing PolicyCraft components...")
    text_processor = TextProcessor()
    theme_extractor = ThemeExtractor()
    policy_classifier = PolicyClassifier()
    _ = DatabaseOperations()
    chart_generator = ChartGenerator()
    recommendation_engine = RecommendationEngine()
    print("✅ All components loaded")
    
    # Dataset paths
    dataset_dir = Path("data/policies/clean_dataset")
    results_dir = Path("data/batch_analysis_results")
    results_dir.mkdir(exist_ok=True)
    
    # Get all policy files
    policy_files = list(dataset_dir.glob("*.pdf")) + list(dataset_dir.glob("*.docx"))
    print(f"\n📄 Found {len(policy_files)} policy files to analyze")
    
    # Results storage
    all_results = []
    failed_analyses = []
    
    # University info mapping
    university_info = {
        'oxford-ai-policy': {'name': 'University of Oxford', 'country': 'UK', 'type': 'Research'},
        'cambridge-ai-policy': {'name': 'University of Cambridge', 'country': 'UK', 'type': 'Research'},
        'mit-ai-policy': {'name': 'MIT', 'country': 'USA', 'type': 'Technical'},
        'stanford-ai-policy': {'name': 'Stanford University', 'country': 'USA', 'type': 'Research'},
        'harvard-ai-policy': {'name': 'Harvard University', 'country': 'USA', 'type': 'Research'},
        'columbia-ai-policy': {'name': 'Columbia University', 'country': 'USA', 'type': 'Research'},
        'imperial-ai-policy': {'name': 'Imperial College London', 'country': 'UK', 'type': 'Technical'},
        'cornell-ai-policy': {'name': 'Cornell University', 'country': 'USA', 'type': 'Research'},
        'chicago-ai-policy': {'name': 'University of Chicago', 'country': 'USA', 'type': 'Research'}
    }
    
    # Process each file
    for i, file_path in enumerate(policy_files, 1):
        print(f"\n{'='*60}")
        print(f"📋 ANALYZING {i}/{len(policy_files)}: {file_path.name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Get university info
            base_name = file_path.stem
            uni_info = university_info.get(base_name, {'name': base_name, 'country': 'Unknown', 'type': 'Unknown'})
            
            print(f"🏛️  University: {uni_info['name']}")
            print(f"🌍 Country: {uni_info['country']}")
            print(f"🎓 Type: {uni_info['type']}")
            
            # STEP 1: Text Extraction
            print(f"\n🔍 STEP 1: Text extraction...")
            extracted_text = text_processor.extract_text_from_file(str(file_path))
            if not extracted_text:
                raise Exception("Text extraction failed")
            print(f"✅ Extracted {len(extracted_text)} characters")
            
            # STEP 2: Text Cleaning
            print(f"🧹 STEP 2: Text cleaning...")
            cleaned_text = text_processor.clean_text(extracted_text)
            print(f"✅ Cleaned to {len(cleaned_text)} characters")
            
            # STEP 3: Theme Extraction
            print(f"🎯 STEP 3: Theme extraction...")
            themes = theme_extractor.extract_themes(cleaned_text)
            print(f"✅ Found {len(themes)} themes")
            for theme in themes[:3]:
                print(f"   - {theme['name']}: {theme['score']} ({theme['confidence']}%)")
            
            # STEP 4: Policy Classification
            print(f"📊 STEP 4: Policy classification...")
            classification = policy_classifier.classify_policy(cleaned_text)
            print(f"✅ Classification: {classification['classification']} ({classification['confidence']}%)")
            
            # STEP 5: Enhanced Recommendation Generation with Full Results Capture
            print(f"💡 STEP 5: Enhanced recommendation generation...")
            recommendations = recommendation_engine.generate_recommendations(
                themes=themes,
                classification=classification,
                text=cleaned_text,
                analysis_id=f"batch_{base_name}"
            )
            
            # Extract comprehensive results from enhanced engine
            rec_summary = recommendations.get('summary', {})
            coverage_analysis = recommendations.get('coverage_analysis', {})
            existing_policies = recommendations.get('existing_policies', {})
            recommendation_list = recommendations.get('recommendations', [])
            
            # Calculate enhanced metrics
            rec_count = len(recommendation_list)
            overall_coverage = rec_summary.get('overall_coverage', 0)
            enhancement_count = rec_summary.get('enhancement_recommendations', 0)
            new_implementations = rec_summary.get('new_implementations', 0)
            existing_policy_count = rec_summary.get('existing_policy_count', 0)
            
            # Extract detailed coverage scores for each ethical dimension
            detailed_coverage = {}
            for dimension, analysis in coverage_analysis.items():
                detailed_coverage[dimension] = {
                    'score': analysis.get('score', 0),
                    'status': analysis.get('status', 'unknown'),
                    'matched_items': len(analysis.get('matched_items', [])),
                    'description': analysis.get('description', '')
                }
            
            # Categorise recommendations by type and priority
            rec_by_priority = {
                'high': len([r for r in recommendation_list if r.get('priority') == 'high']),
                'medium': len([r for r in recommendation_list if r.get('priority') == 'medium']),
                'low': len([r for r in recommendation_list if r.get('priority') == 'low'])
            }
            
            rec_by_type = {
                'enhancement': len([r for r in recommendation_list if r.get('implementation_type') == 'enhancement']),
                'new': len([r for r in recommendation_list if r.get('implementation_type') == 'new']),
                'review': len([r for r in recommendation_list if r.get('implementation_type') == 'review'])
            }
            
            # Extract key existing policies detected
            key_existing_policies = []
            for policy_type, exists in existing_policies.items():
                if exists:
                    key_existing_policies.append(policy_type.replace('_', ' ').title())
            
            # Enhanced console output with meaningful information
            print(f"✅ Generated {rec_count} contextual recommendations")
            print(f"✅ Overall coverage: {overall_coverage}% (realistic scoring)")
            print(f"📊 Dimension scores: " + " | ".join([
                f"{dim.replace('_', ' ').title()}: {data['score']:.1f}%" 
                for dim, data in detailed_coverage.items()
            ]))
            print(f"🏛️ Existing policies detected: {existing_policy_count} ({', '.join(key_existing_policies[:3])})")
            print(f"🔧 Recommendation mix: {enhancement_count} enhancements, {new_implementations} new implementations")
            
            # STEP 6: Generate Charts
            print(f"📈 STEP 6: Chart generation...")
            charts = chart_generator.generate_analysis_charts(themes, classification)
            print(f"✅ Generated {len(charts)} charts")
            
            # Calculate processing time
            processing_time = round(time.time() - start_time, 2)
            print(f"⏱️  Processing time: {processing_time}s")
            
            # Enhanced Results Storage with Full Recommendation Data
            result = {
                'university': uni_info['name'],
                'country': uni_info['country'],
                'type': uni_info['type'],
                'filename': file_path.name,
                'file_size_kb': round(file_path.stat().st_size / 1024, 2),
                'processing_time': processing_time,
                'text_stats': {
                    'original_length': len(extracted_text),
                    'cleaned_length': len(cleaned_text),
                    'compression_ratio': round(len(cleaned_text) / len(extracted_text), 3)
                },
                'themes': {
                    'count': len(themes),
                    'top_themes': [t['name'] for t in themes[:5]],
                    'avg_confidence': round(sum(t['confidence'] for t in themes) / len(themes), 1) if themes else 0,
                    'all_themes': [{'name': t['name'], 'score': t['score'], 'confidence': t['confidence']} for t in themes]
                },
                'classification': {
                    'type': classification['classification'],
                    'confidence': classification['confidence'],
                    'method': classification.get('method', 'unknown')
                },
                # ENHANCED: Full recommendation analysis instead of just counts
                'recommendations': {
                    'count': rec_count,
                    'overall_coverage': overall_coverage,
                    'priority_breakdown': rec_by_priority,
                    'type_breakdown': rec_by_type,
                    'enhancement_count': enhancement_count,
                    'new_implementation_count': new_implementations,
                    'detailed_recommendations': [
                        {
                            'title': r.get('title', 'Untitled'),
                            'description': r.get('description', '')[:200] + '...' if len(r.get('description', '')) > 200 else r.get('description', ''),
                            'dimension': r.get('dimension', 'general'),
                            'priority': r.get('priority', 'medium'),
                            'implementation_type': r.get('implementation_type', 'new'),
                            'timeframe': r.get('timeframe', 'TBD'),
                            'source': r.get('source', 'PolicyCraft')
                        } for r in recommendation_list
                    ]
                },
                # NEW: Detailed ethical coverage analysis
                'ethical_coverage': {
                    'overall_score': overall_coverage,
                    'dimension_scores': {
                        dim: data['score'] for dim, data in detailed_coverage.items()
                    },
                    'dimension_status': {
                        dim: data['status'] for dim, data in detailed_coverage.items()
                    },
                    'strong_areas': [
                        dim.replace('_', ' ').title() for dim, data in detailed_coverage.items() 
                        if data['status'] == 'strong'
                    ],
                    'weak_areas': [
                        dim.replace('_', ' ').title() for dim, data in detailed_coverage.items() 
                        if data['status'] == 'weak'
                    ],
                    'coverage_details': detailed_coverage
                },
                # NEW: Existing policy detection results
                'existing_policies': {
                    'total_detected': existing_policy_count,
                    'policy_types': key_existing_policies,
                    'detailed_detection': existing_policies
                },
                # Enhanced metadata
                'analysis_metadata': {
                    'engine_version': recommendations.get('analysis_metadata', {}).get('framework_version', '2.0-enhanced'),
                    'methodology': recommendations.get('analysis_metadata', {}).get('methodology', 'Enhanced Ethical Framework Analysis'),
                    'academic_sources': recommendations.get('analysis_metadata', {}).get('academic_sources', ['UNESCO 2023', 'JISC 2023', 'BERA 2018']),
                    'fixes_applied': recommendations.get('analysis_metadata', {}).get('fixes_applied', [])
                },
                'charts_generated': len(charts),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            all_results.append(result)
            print(f"✅ Enhanced analysis completed successfully!")
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            failed_analyses.append({
                'filename': file_path.name,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    # Generate summary report
    print(f"\n{'='*60}")
    print("📊 BATCH ANALYSIS SUMMARY")
    print(f"{'='*60}")
    
    successful = len(all_results)
    failed = len(failed_analyses)
    total = successful + failed
    
    print(f"✅ Successful analyses: {successful}/{total} ({(successful/total*100):.1f}%)")
    print(f"❌ Failed analyses: {failed}/{total} ({(failed/total*100):.1f}%)")
    
    if successful > 0:
        # Calculate aggregate statistics
        avg_processing_time = round(sum(r['processing_time'] for r in all_results) / successful, 2)
        avg_themes_count = round(sum(r['themes']['count'] for r in all_results) / successful, 1)
        avg_confidence = round(sum(r['classification']['confidence'] for r in all_results) / successful, 1)
        avg_coverage = round(sum(r['recommendations']['overall_coverage'] for r in all_results) / successful, 1)
        
        print(f"\n📈 AGGREGATE STATISTICS:")
        print(f"   ⏱️  Average processing time: {avg_processing_time}s")
        print(f"   🎯 Average themes per policy: {avg_themes_count}")
        print(f"   📊 Average classification confidence: {avg_confidence}%")
        print(f"   💡 Average coverage score: {avg_coverage}%")
        
        # Classification distribution
        classifications = [r['classification']['type'] for r in all_results]
        classification_counts = {cls: classifications.count(cls) for cls in set(classifications)}
        print(f"\n🏷️  CLASSIFICATION DISTRIBUTION:")
        for cls, count in classification_counts.items():
            print(f"   {cls}: {count} policies ({count/successful*100:.1f}%)")
        
        # Country breakdown
        countries = [r['country'] for r in all_results]
        country_counts = {country: countries.count(country) for country in set(countries)}
        print(f"\n🌍 COUNTRY BREAKDOWN:")
        for country, count in country_counts.items():
            print(f"   {country}: {count} policies")
    
    # Save detailed results
    results_file = results_dir / f"batch_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            'summary': {
                'total_files': total,
                'successful': successful,
                'failed': failed,
                'success_rate': successful/total*100 if total > 0 else 0,
                'analysis_date': datetime.now().isoformat()
            },
            'results': all_results,
            'failed_analyses': failed_analyses
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Create CSV summary for easy analysis
    if all_results:
        _ = pd.DataFrame(all_results)
        csv_file = results_dir / f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Flatten nested data for CSV
        csv_data = []
        for result in all_results:
            row = {
                'University': result['university'],
                'Country': result['country'],
                'Type': result['type'],
                'Filename': result['filename'],
                'File_Size_KB': result['file_size_kb'],
                'Processing_Time_Sec': result['processing_time'],
                'Text_Original_Length': result['text_stats']['original_length'],
                'Text_Cleaned_Length': result['text_stats']['cleaned_length'],
                'Theme_Count': result['themes']['count'],
                'Avg_Theme_Confidence': result['themes']['avg_confidence'],
                'Classification_Type': result['classification']['type'],
                'Classification_Confidence': result['classification']['confidence'],
                'Recommendations_Count': result['recommendations']['count'],
                'Coverage_Score': result['recommendations']['coverage_score'],
                'High_Priority_Recs': result['recommendations']['high_priority_count']
            }
            csv_data.append(row)
        
        generate_enhanced_csv_summary(all_results, csv_file)
        print(f"📈 CSV summary saved to: {csv_file}")
    
    print(f"\n🎉 BATCH ANALYSIS COMPLETED!")
    print(f"Ready for validation and report writing! 📝")
    
    return all_results

# CSV generation section with enhanced fields

def generate_enhanced_csv_summary(all_results, csv_file):
    """Generate enhanced CSV summary with detailed ethical coverage metrics."""
    csv_data = []
    
    for result in all_results:
        # Extract enhanced metrics
        ethical_coverage = result.get('ethical_coverage', {})
        recommendations = result.get('recommendations', {})
        existing_policies = result.get('existing_policies', {})
        
        row = {
            # Basic information
            'University': result['university'],
            'Country': result['country'],
            'Type': result['type'],
            'Filename': result['filename'],
            'File_Size_KB': result['file_size_kb'],
            'Processing_Time_Sec': result['processing_time'],
            
            # Text statistics
            'Text_Original_Length': result['text_stats']['original_length'],
            'Text_Cleaned_Length': result['text_stats']['cleaned_length'],
            
            # Theme analysis
            'Theme_Count': result['themes']['count'],
            'Avg_Theme_Confidence': result['themes']['avg_confidence'],
            
            # Classification
            'Classification_Type': result['classification']['type'],
            'Classification_Confidence': result['classification']['confidence'],
            
            # ENHANCED: Detailed recommendation metrics
            'Recommendations_Count': recommendations.get('count', 0),
            'Overall_Coverage_Score': recommendations.get('overall_coverage', 0),
            'High_Priority_Recs': recommendations.get('priority_breakdown', {}).get('high', 0),
            'Medium_Priority_Recs': recommendations.get('priority_breakdown', {}).get('medium', 0),
            'Enhancement_Recs': recommendations.get('enhancement_count', 0),
            'New_Implementation_Recs': recommendations.get('new_implementation_count', 0),
            
            # NEW: Ethical dimension scores
            'Accountability_Score': ethical_coverage.get('dimension_scores', {}).get('accountability', 0),
            'Transparency_Score': ethical_coverage.get('dimension_scores', {}).get('transparency', 0),
            'Human_Agency_Score': ethical_coverage.get('dimension_scores', {}).get('human_agency', 0),
            'Inclusiveness_Score': ethical_coverage.get('dimension_scores', {}).get('inclusiveness', 0),
            
            # NEW: Policy detection metrics
            'Existing_Policies_Count': existing_policies.get('total_detected', 0),
            'Has_Disclosure_Requirements': existing_policies.get('detailed_detection', {}).get('disclosure_requirements', False),
            'Has_Governance_Structure': existing_policies.get('detailed_detection', {}).get('governance_structure', False),
            'Has_Approval_Processes': existing_policies.get('detailed_detection', {}).get('approval_processes', False),
            
            # Quality indicators
            'Strong_Ethical_Areas_Count': len(ethical_coverage.get('strong_areas', [])),
            'Weak_Ethical_Areas_Count': len(ethical_coverage.get('weak_areas', [])),
            'Engine_Version': result.get('analysis_metadata', {}).get('engine_version', 'unknown')
        }
        csv_data.append(row)
    
    # Export to CSV with enhanced metrics
    import pandas as pd
    df = pd.DataFrame(csv_data)
    df.to_csv(csv_file, index=False)
    print(f"📈 Enhanced CSV summary saved with {len(df.columns)} metrics: {csv_file}")
    
    # Print summary of enhanced metrics
    print(f"\n🔍 ENHANCED METRICS SUMMARY:")
    print(f"   📊 Average overall coverage: {df['Overall_Coverage_Score'].mean():.1f}%")
    print(f"   🎯 Average recommendations per policy: {df['Recommendations_Count'].mean():.1f}")
    print(f"   🔧 Enhancement vs New ratio: {df['Enhancement_Recs'].sum()}:{df['New_Implementation_Recs'].sum()}")
    print(f"   🏛️ Policies with existing governance: {df['Has_Governance_Structure'].sum()}/{len(df)}")
    print(f"   📋 Policies with disclosure requirements: {df['Has_Disclosure_Requirements'].sum()}/{len(df)}")
    
    # Dimensional analysis
    dimension_averages = {
        'Accountability': df['Accountability_Score'].mean(),
        'Transparency': df['Transparency_Score'].mean(), 
        'Human Agency': df['Human_Agency_Score'].mean(),
        'Inclusiveness': df['Inclusiveness_Score'].mean()
    }
    
    print(f"\n📈 ETHICAL DIMENSION AVERAGES:")
    for dimension, avg_score in dimension_averages.items():
        print(f"   {dimension}: {avg_score:.1f}%")
    
    return df

if __name__ == "__main__":
    run_batch_analysis()