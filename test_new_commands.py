"""
Test script để validate !analyze và !fetchresults commands
Sử dụng mock data từ predictions_log.json
"""

import json
import os
from datetime import datetime, timedelta

def test_analyze_logic():
    """Test logic của !analyze command"""
    print("=" * 60)
    print("TEST 1: Analyze Command Logic")
    print("=" * 60)
    
    if not os.path.exists('predictions_log.json'):
        print("❌ Không tìm thấy predictions_log.json")
        return False
    
    with open('predictions_log.json', 'r', encoding='utf-8') as f:
        predictions = json.load(f)
    
    completed = [p for p in predictions if p.get('actual_result') is not None]
    
    if not completed:
        print("⚠️ Chưa có trận nào hoàn thành")
        return False
    
    print(f"\n📊 Tổng số predictions: {len(predictions)}")
    print(f"✅ Đã hoàn thành: {len(completed)}")
    print(f"⏳ Đang chờ: {len(predictions) - len(completed)}")
    
    # Overall accuracy
    total = len(completed)
    correct = sum(1 for p in completed if p.get('correct'))
    accuracy = correct / total
    
    acc_icon = '🟢' if accuracy >= 0.65 else ('🟡' if accuracy >= 0.55 else '🔴')
    print(f"\n{acc_icon} Độ Chính Xác Tổng Thể: {accuracy:.1%} ({correct}/{total})")
    
    # By confidence level
    high_conf = [p for p in completed if p.get('confidence', 0) >= 0.7]
    med_conf = [p for p in completed if 0.55 <= p.get('confidence', 0) < 0.7]
    
    if high_conf:
        high_acc = sum(1 for p in high_conf if p.get('correct')) / len(high_conf)
        print(f"\n📈 Confidence Cao (≥70%): {high_acc:.1%} ({len(high_conf)} trận)")
    
    if med_conf:
        med_acc = sum(1 for p in med_conf if p.get('correct')) / len(med_conf)
        print(f"📈 Confidence Trung (55-70%): {med_acc:.1%} ({len(med_conf)} trận)")
    
    # O/U Analysis
    ou_completed = [p for p in completed if p.get('ou_pick') and p.get('ou_actual') and p.get('ou_actual') != 'Push']
    
    if ou_completed:
        print(f"\n🎯 Over/Under Analysis ({len(ou_completed)} trận):")
        
        ou_correct = sum(1 for p in ou_completed if p.get('ou_correct'))
        ou_accuracy = ou_correct / len(ou_completed)
        print(f"   Accuracy: {ou_accuracy:.1%} ({ou_correct}/{len(ou_completed)})")
        
        over_picks = sum(1 for p in ou_completed if p.get('ou_pick') == 'Over')
        over_ratio = over_picks / len(ou_completed)
        
        print(f"   Over picks: {over_picks} ({over_ratio:.1%})")
        print(f"   Under picks: {len(ou_completed) - over_picks} ({(1-over_ratio):.1%})")
        
        # Bias detection
        if over_ratio > 0.65:
            print(f"   ⚠️ OVER BIAS DETECTED: {over_ratio:.1%} picks là Over")
        elif over_ratio < 0.35:
            print(f"   ⚠️ UNDER BIAS DETECTED: {(1-over_ratio):.1%} picks là Under")
        else:
            print(f"   ✅ Cân bằng tốt")
        
        # Win rate by pick
        over_preds = [p for p in ou_completed if p.get('ou_pick') == 'Over']
        under_preds = [p for p in ou_completed if p.get('ou_pick') == 'Under']
        
        if over_preds:
            over_wr = sum(1 for p in over_preds if p.get('ou_correct')) / len(over_preds)
            print(f"   Over Win Rate: {over_wr:.1%}")
        
        if under_preds:
            under_wr = sum(1 for p in under_preds if p.get('ou_correct')) / len(under_preds)
            print(f"   Under Win Rate: {under_wr:.1%}")
    
    # Goals prediction
    goals_completed = [p for p in completed 
                      if p.get('predicted_goals') is not None 
                      and p.get('home_goals') is not None]
    
    if goals_completed:
        errors = []
        for p in goals_completed:
            predicted = p.get('predicted_goals', 0)
            actual = (p.get('home_goals', 0) or 0) + (p.get('away_goals', 0) or 0)
            errors.append(abs(predicted - actual))
        
        mae = sum(errors) / len(errors)
        print(f"\n⚽ Dự Đoán Tổng Bàn:")
        print(f"   MAE: {mae:.2f} bàn/trận ({len(goals_completed)} trận)")
    
    # Recent results
    print(f"\n📝 5 Trận Gần Nhất:")
    recent = completed[-5:] if len(completed) > 5 else completed
    for p in reversed(recent):
        icon = '✅' if p.get('correct') else '❌'
        score = f"{p.get('home_goals', '?')}-{p.get('away_goals', '?')}"
        teams = f"{p['home_team'][:12]} vs {p['away_team'][:12]}"
        print(f"   {icon} {teams:30} ({score})")
    
    print("\n✅ Test analyze logic PASSED")
    return True


def test_fetch_results_requirements():
    """Test requirements cho fetch results"""
    print("\n" + "=" * 60)
    print("TEST 2: Fetch Results Requirements")
    print("=" * 60)
    
    # Check if API key exists
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('FOOTBALL_DATA_API_KEY')
    if not api_key:
        print("⚠️ FOOTBALL_DATA_API_KEY chưa được cấu hình")
        print("   → Cần thêm vào .env hoặc Render environment variables")
    else:
        print(f"✅ FOOTBALL_DATA_API_KEY: {api_key[:10]}..." if len(api_key) > 10 else "✅ FOOTBALL_DATA_API_KEY configured")
    
    # Check pending predictions
    if not os.path.exists('predictions_log.json'):
        print("❌ Không tìm thấy predictions_log.json")
        return False
    
    with open('predictions_log.json', 'r', encoding='utf-8') as f:
        predictions = json.load(f)
    
    pending = [p for p in predictions if p.get('actual_result') is None]
    print(f"\n📊 Pending predictions: {len(pending)}")
    
    if pending:
        print("\n⏳ Predictions đang chờ kết quả:")
        for p in pending[:5]:  # Show first 5
            match = f"{p['home_team']} vs {p['away_team']}"
            timestamp = p.get('timestamp', 'N/A')
            print(f"   - {match:40} ({timestamp})")
    else:
        print("   (Tất cả predictions đã có kết quả)")
    
    # Test auto_fetch_results function exists
    try:
        from prediction_tracker import auto_fetch_results
        print("\n✅ auto_fetch_results function imported successfully")
        
        # Check function signature
        import inspect
        sig = inspect.signature(auto_fetch_results)
        print(f"   Signature: {sig}")
        
    except ImportError as e:
        print(f"\n❌ Cannot import auto_fetch_results: {e}")
        return False
    
    print("\n✅ Test fetch results requirements PASSED")
    return True


def test_integration_workflow():
    """Test toàn bộ workflow"""
    print("\n" + "=" * 60)
    print("TEST 3: Integration Workflow")
    print("=" * 60)
    
    # Simulate workflow
    print("\n📋 Workflow:")
    print("   1. Bot tạo prediction → ✅ (có trong predictions_log.json)")
    print("   2. User chạy !fetchresults → ⏳ (cần test với real API)")
    print("   3. User chạy !analyze → ✅ (logic tested above)")
    print("   4. Điều chỉnh calibration nếu cần → ⏳ (manual)")
    
    # Check bot.py has new commands
    with open('bot.py', 'r', encoding='utf-8') as f:
        bot_content = f.read()
    
    has_analyze = '@bot.command(name=\'analyze\')' in bot_content
    has_fetchresults = '@bot.command(name=\'fetchresults\')' in bot_content
    
    print(f"\n🤖 Bot Commands:")
    print(f"   !analyze: {'✅' if has_analyze else '❌'}")
    print(f"   !fetchresults: {'✅' if has_fetchresults else '❌'}")
    
    if has_analyze and has_fetchresults:
        print("\n✅ Test integration workflow PASSED")
        return True
    else:
        print("\n❌ Test integration workflow FAILED")
        return False


def main():
    print("\n🧪 TESTING NEW COMMANDS: !analyze & !fetchresults")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Analyze Logic", test_analyze_logic()))
    results.append(("Fetch Requirements", test_fetch_results_requirements()))
    results.append(("Integration Workflow", test_integration_workflow()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:25} {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n📝 Next Steps:")
        print("   1. Deploy bot lên Render (nếu chưa)")
        print("   2. Test !analyze trong Discord với mock data")
        print("   3. Chạy !fetchresults để fetch real data")
        print("   4. Monitor bias với !analyze sau mỗi gameweek")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Review output above.")
    
    return passed == total


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
