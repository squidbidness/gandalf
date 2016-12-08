#ifndef VECTOR_HPP_DA39A3EE
#define VECTOR_HPP_DA39A3EE

#include <algorithm>
#include <array>
#include <initializer_list>

namespace geo {

	template< typename T, size_t N >
	struct Vector : std::array<T, N> {

		constexpr T &x() {
			static_assert( N > 0 );
			return std::get<0>( *this );
		}
		constexpr T const &x() const {
			return x();
		}

		constexpr T &y() {
			static_assert( N > 1 );
			return std::get<1>( *this );
		}
		constexpr T const &y() const {
			return y();
		}

		constexpr T &z() {
			static_assert( N > 2 );
			return std::get<2>( *this );
		}
		constexpr T const &z() const {
			return z();
		}

		constexpr T &w() {
			static_assert( N > 3 );
			return std::get<3>( *this );
		}
		constexpr T const &w() const {
			return w();
		}

	};

	template< typename ...T >
	constexpr auto makeVector( T &&...t ) {
		return Vector< std::common_type_t<T...>, sizeof...(T) >{
				std::forward<T>( t )... };
	}

	template< typename T, typename S, size_t N, size_t ...I >
	constexpr auto dot( Vector<T, N> const &a, Vector<S, N> const &b,
			std::index_sequence<I...> = std::make_index_sequence<N>() )
	{
		return ( ( std::get<I>(a) * std::get<I>(b) ) + ... );
	}


	template< size_t N > using VectorF = Vector<float, N>;
	template< size_t N > using VectorD = Vector<double, N>;

	template< typename T > using Vector1 = Vector<T, 1>;
	template< typename T > using Vector2 = Vector<T, 2>;
	template< typename T > using Vector3 = Vector<T, 3>;
	template< typename T > using Vector4 = Vector<T, 4>;

	using VectorF1 = VectorF<1>;
	using VectorF2 = VectorF<2>;
	using VectorF3 = VectorF<3>;
	using VectorF4 = VectorF<4>;

	using VectorD1 = VectorD<1>;
	using VectorD2 = VectorD<2>;
	using VectorD3 = VectorD<3>;
	using VectorD4 = VectorD<4>;

	namespace Vector_shorthand {
		constexpr auto V_ = [] ( auto &&...t ) {
			return makeVector( std::forward<decltype(t)>( t )... );
		};
	}
}

#endif
